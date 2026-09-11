"""W71878 -- the target-global integration coordinator.

WHAT THESE CASES ARE ABOUT. One canonical target's queue order, and the single
live lease that decides who may mutate it. They are NOT about eligibility
(PLAN item 4), Git (item 5) or Authority completion (item 6): no case here
touches a working tree, and the eligibility account is a fixture because this
seam stores it rather than proving it.

THE CASE THIS RECORD'S ACCEPTANCE CLAUSE NAMES is
`TwoAuthoritiesContendOnOneLock`. W83781 binds each `JobStore` immutably to one
Authority UUID, so a live-target index there is unique only WITHIN one
Authority. The owner ruled on 2026-09-05 that this store sits outside every
such binding; that class is what proves the ruling was carried out rather than
described.

THE CLASSES AT THE BOTTOM ARE THE REVIEW ROUNDS OF 2026-09-06, in order. Every
reproduction those reviews drove is re-enacted here as a refusal -- premature
release, the cross-wired block, split persisted evidence, the store adopted
without its own safety index, the erased block, the reset lifecycle, the
deleted history, the rewritten signed act, the unproved retry and the reversed
queue -- because a defect a suite cannot re-enact is one a later change can
restore. The last class is not a review's: it is the owner's VCS-neutrality
clarification, kept as a gate over this package's own names.
"""

import os
import sqlite3
import stat
import threading
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.integration import (IntegrationStore, SCHEMA_VERSION,
                                   TARGET_SCHEMA, abandon_lease,
                                   activate_target, block_target, enqueue,
                                   entries_of, grant_lease, lease_of,
                                   live_grant, refuse_entry, release_lease,
                                   settle_integrated, target_of)

from baton_v12.integration import schema
from baton_v12.integration.store import integration_signature

from .fixtures import (DESCRIPTION, LATER, NOW, TARGET, UUID_A, UUID_B,
                       CoordinatorCase, eligibility, target)

SETTLEMENT = {"imported_paths": ["src/a.py"],
              "verification": {"final_bytes": "checked"}}
REFUSAL = {"reason": "scope",
           "detail": {"path": "outside the reviewed set"}}
INTEGRATED = {"outcome": "integrated"}


class QueueCase(CoordinatorCase):
    """A store with one activated target, which nearly every case needs."""

    def setUp(self):
        super().setUp()
        self.coordinator = self.store()
        activate_target(self.coordinator, target())

    def place(self, entry_id, **operands):
        return enqueue(self.coordinator, canonical_target_id=TARGET,
                       entry_id=entry_id, eligibility=eligibility(**operands))

    def lease(self, lease_id="lease-1", participant="baton.integrator",
              attempt_id="attempt-1", canonical_target_id=TARGET,
              entry_id=None):
        if entry_id is None:
            existing = lease_of(self.coordinator, lease_id)
            queued = entries_of(self.coordinator, canonical_target_id,
                                state="queued")
            entry_id = (existing["entry_id"] if existing is not None else
                        min(queued, key=lambda one: one["rank"])["entry_id"]
                        if queued else "entry-absent")
        return grant_lease(self.coordinator,
                           canonical_target_id=canonical_target_id,
                           entry_id=entry_id,
                           lease_id=lease_id,
                           integrator_participant=participant,
                           attempt_id=attempt_id)

    def integrate(self, entry_id, lease_id, fence):
        """The whole ordinary success path: settle, then release."""
        settle_integrated(self.coordinator, lease_id=lease_id,
                          canonical_target_id=TARGET, fence=fence,
                          entry_id=entry_id, settlement=SETTLEMENT)
        return release_lease(self.coordinator, lease_id=lease_id,
                             canonical_target_id=TARGET, entry_id=entry_id,
                             fence=fence, ending=INTEGRATED)

    def block(self, entry_id, lease_id, fence, reason="integrity",
              detail=None):
        return block_target(self.coordinator, canonical_target_id=TARGET,
                            entry_id=entry_id, lease_id=lease_id, fence=fence,
                            reason=reason,
                            detail={"observed": "a mixed working tree"}
                            if detail is None else detail)

    def states(self):
        return [one["state"] for one in entries_of(self.coordinator, TARGET)]

    def live(self):
        return [row["lease_id"] for row in self.coordinator._connection.execute(
            "SELECT lease_id FROM leases WHERE state = 'live'")]


class TargetIdentityIsConfigurationS(QueueCase):

    def test_an_activated_target_is_found_by_its_configured_key(self):
        found = target_of(self.coordinator, TARGET)
        self.assertEqual(found["state"], "open")
        self.assertEqual(found["fence"], 0)
        self.assertEqual(found["document"]["description"], DESCRIPTION)

    def test_the_key_is_not_derived_from_any_narrower_identity(self):
        """The defect this guards is one target acquiring two locks.

        A line, Work, proposal or checkpoint is scoped more narrowly than a
        target, so a key derived from one of them would make one of these
        lookups find a target. None of them is a key here.
        """
        account = eligibility()
        for narrower in ("line_id", "work_id", "proposal_id", "checkpoint_id",
                         "authority_uuid", "expected_target_revision"):
            self.assertIsNone(target_of(self.coordinator, account[narrower]),
                              narrower)

    def test_repeating_the_same_activation_is_one_act(self):
        again = activate_target(self.coordinator, target())
        self.assertEqual(again, target_of(self.coordinator, TARGET))

    def test_one_target_id_is_not_re_described_under_another_document(self):
        caught = self.refusal(activate_target, self.coordinator,
                              target(description="somewhere else entirely"))
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertEqual(target_of(self.coordinator, TARGET)
                         ["document"]["description"], DESCRIPTION)

    def test_a_document_of_another_schema_is_not_a_target(self):
        wrong = target()
        wrong["schema"] = "baton.v12.integration-target/99"
        caught = self.refusal(activate_target, self.coordinator, wrong)
        self.assertEqual(caught.category, "integrity")
        self.assertIn(TARGET_SCHEMA, caught.message)

    def test_an_entry_belongs_to_a_configured_target(self):
        caught = self.refusal(
            enqueue, self.coordinator, canonical_target_id="target:unknown",
            entry_id="entry-1", eligibility=eligibility())
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))


class RankIsAllocatedInTheEnqueueTransaction(QueueCase):

    def test_rank_counts_from_one_in_arrival_order(self):
        self.assertEqual([self.place("entry-1", checkpoint_id="c-1")["rank"],
                          self.place("entry-2", checkpoint_id="c-2")["rank"],
                          self.place("entry-3", checkpoint_id="c-3")["rank"]],
                         [1, 2, 3])

    def test_an_exact_replay_returns_the_same_entry_and_the_same_rank(self):
        first = self.place("entry-1")
        self.assertEqual(self.place("entry-1"), first)
        self.assertEqual(len(entries_of(self.coordinator, TARGET)), 1)

    def test_the_same_entry_id_with_other_operands_collides(self):
        self.place("entry-1")
        caught = self.refusal(enqueue, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-1",
                              eligibility=eligibility(verdict_id="verdict-9"))
        self.assertEqual(caught.code, "operation-collision")

    def test_one_candidate_does_not_take_a_second_place_in_the_queue(self):
        """A second entry id for one candidate, which the index would answer
        with a raw `sqlite3.IntegrityError` if this were left to it."""
        first = self.place("entry-1")
        caught = self.refusal(enqueue, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-2",
                              eligibility=eligibility())
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertIn("entry-1", caught.message)
        self.assertEqual([one["entry_id"] for one in
                          entries_of(self.coordinator, TARGET)],
                         [first["entry_id"]])

    def test_an_account_missing_an_operand_never_reaches_the_queue(self):
        short = eligibility()
        del short["scope_digest"]
        caught = self.refusal(enqueue, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-1",
                              eligibility=short)
        self.assertEqual(caught.category, "integrity")
        self.assertEqual(entries_of(self.coordinator, TARGET), [])

    def test_a_generation_that_looks_like_a_number_is_not_one(self):
        """§4 compares a generation as part of an identity, and text reaching
        an INTEGER column is a `sqlite3.IntegrityError` no caller can act on."""
        caught = self.refusal(enqueue, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-1",
                              eligibility=eligibility(assignment_generation="1"))
        self.assertEqual(caught.category, "integrity")

    def test_an_authority_namespace_is_an_authority_identity(self):
        """Review of 2026-09-06 [P1]: `not-an-authority` was accepted and
        returned by a store whose entries the contract calls
        Authority-namespaced."""
        caught = self.refusal(enqueue, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-1",
                              eligibility=eligibility(
                                  authority_uuid="not-an-authority"))
        self.assertEqual(caught.category, "integrity")
        self.assertIn("32 lowercase hexadecimal", caught.message)
        self.assertEqual(entries_of(self.coordinator, TARGET), [])

    def test_both_digest_families_are_retained_and_neither_is_derived(self):
        entry = self.place("entry-1")
        self.assertNotEqual(entry["checkpoint_digest"],
                            entry["candidate_digest"])
        self.assertNotEqual(entry["checkpoint_digest"],
                            entry["result_digest"])
        self.assertEqual(entry["eligibility"], eligibility())


class TwoAuthoritiesContendOnOneLock(QueueCase):
    """The acceptance clause: distinct Authorities, one target, one lock."""

    def setUp(self):
        super().setUp()
        self.a = self.place("entry-a", authority_uuid=UUID_A,
                            checkpoint_id="c-a")
        self.b = self.place("entry-b", authority_uuid=UUID_B,
                            checkpoint_id="c-b", line_id="line-2")

    def test_entries_from_two_authorities_share_one_ordered_queue(self):
        self.assertEqual([(one["authority_uuid"], one["rank"]) for one in
                          entries_of(self.coordinator, TARGET)],
                         [(UUID_A, 1), (UUID_B, 2)])

    def test_one_lease_is_live_across_both_authorities(self):
        granted = self.lease("lease-1")
        self.assertEqual(granted["entry"]["entry_id"], "entry-a")
        self.assertIsNone(self.lease("lease-2"))

    def test_the_other_authority_is_offered_the_target_only_in_turn(self):
        first = self.lease("lease-1")
        self.integrate("entry-a", "lease-1", first["lease"]["fence"])
        second = self.lease("lease-2")
        self.assertEqual(second["entry"]["entry_id"], "entry-b")
        self.assertEqual(second["entry"]["authority_uuid"], UUID_B)

    def test_the_store_records_no_authority_binding_to_be_bound_by(self):
        """A binding here would put the defect back one layer down.

        `IntegrationStore.open` takes no Authority, and reopening the same
        file under a different incarnation adopts it rather than refusing it
        the way an Authority-bound `JobStore` refuses a foreign one.
        """
        again = self.store(incarnation="coordinator-2")
        self.assertEqual([one["entry_id"] for one in
                          entries_of(again, TARGET)],
                         ["entry-a", "entry-b"])


class OneLiveLeasePerTarget(QueueCase):

    def setUp(self):
        super().setUp()
        self.first = self.place("entry-1", checkpoint_id="c-1")
        self.second = self.place("entry-2", checkpoint_id="c-2")

    def test_a_grant_takes_the_smallest_queued_rank(self):
        granted = self.lease()
        self.assertEqual(granted["entry"]["rank"], 1)
        self.assertEqual(granted["entry"]["state"], "leased")
        self.assertEqual(granted["lease"]["fence"], 1)

    def test_an_empty_queue_grants_nothing_and_burns_no_fence(self):
        empty = self.store(path=self.path + ".empty")
        activate_target(empty, target(canonical_target_id="target:empty"))
        self.assertIsNone(grant_lease(empty,
                                      canonical_target_id="target:empty",
                                      entry_id="entry-1",
                                      lease_id="lease-1",
                                      integrator_participant="baton.integrator",
                                      attempt_id="attempt-1"))
        self.assertEqual(target_of(empty, "target:empty")["fence"], 0)

    def test_the_fence_increases_with_every_grant_that_ever_existed(self):
        first = self.lease("lease-1")
        refuse_entry(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", settlement=REFUSAL,
                     lease_id="lease-1", fence=first["lease"]["fence"])
        second = self.lease("lease-2")
        self.assertEqual((first["lease"]["fence"], second["lease"]["fence"]),
                         (1, 2))
        self.assertEqual(target_of(self.coordinator, TARGET)["fence"], 2)

    def test_a_grant_replays_rather_than_leasing_a_second_entry(self):
        first = self.lease("lease-1")
        self.assertEqual(self.lease("lease-1"), first)
        self.assertEqual(self.states(), ["leased", "queued"])

    def test_two_grants_race_and_the_store_decides(self):
        """Not "both read no live lease and both write one".

        Each thread owns its own connection to one file, so the exclusion is
        the partial unique index and `BEGIN IMMEDIATE` rather than anything
        this process serializes for them.
        """
        answers = {}
        barrier = threading.Barrier(2)

        def contend(name):
            store = IntegrationStore.open(self.path, incarnation=name,
                                          clock=self.clock)
            try:
                barrier.wait()
                answers[name] = grant_lease(
                    store, canonical_target_id=TARGET, entry_id="entry-1",
                    lease_id="lease-" + name,
                    integrator_participant="baton." + name,
                    attempt_id="attempt-" + name)
            except ContractRefusal as refusal:
                answers[name] = refusal
            except sqlite3.OperationalError as failure:
                answers[name] = failure
            finally:
                store.close()

        threads = [threading.Thread(target=contend, args=(name,))
                   for name in ("one", "two")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        granted = [name for name, answer in answers.items()
                   if isinstance(answer, dict)]
        refused = [answer for answer in answers.values()
                   if isinstance(answer, ContractRefusal)]
        self.assertEqual(len(granted), 1, answers)
        self.assertEqual(refused, [])
        self.assertEqual(sum(answer is None for answer in answers.values()), 1)
        self.assertEqual(len(self.live()), 1)


class DistinctTargetsDoNotSerializeEachOther(CoordinatorCase):

    def test_two_targets_hold_live_leases_at_the_same_time(self):
        store = self.store()
        for name in ("target:one", "target:two"):
            activate_target(store, target(canonical_target_id=name,
                                          description="target " + name))
            enqueue(store, canonical_target_id=name, entry_id="entry-" + name,
                    eligibility=eligibility(checkpoint_id="c-" + name))
        leases = [grant_lease(store, canonical_target_id=name,
                              entry_id="entry-" + name,
                              lease_id="lease-" + name,
                              integrator_participant="baton.integrator",
                              attempt_id="attempt-" + name)
                  for name in ("target:one", "target:two")]
        self.assertEqual([one["lease"]["state"] for one in leases],
                         ["live", "live"])
        self.assertEqual([one["lease"]["fence"] for one in leases], [1, 1])


class AGrantIsProvedLiveWhereItIsUsed(QueueCase):
    """`live_grant` exists because operands are values and values replay."""

    def setUp(self):
        super().setUp()
        self.place("entry-1")
        self.granted = self.lease("lease-1")
        self.fence = self.granted["lease"]["fence"]

    def held(self, **replaced):
        operands = {"lease_id": "lease-1", "canonical_target_id": TARGET,
                    "entry_id": "entry-1", "fence": self.fence}
        operands.update(replaced)
        return live_grant(self.coordinator, **operands)

    def test_the_holder_passes(self):
        self.assertEqual(self.held()["lease_id"], "lease-1")

    def test_a_stale_fence_does_not_pass(self):
        caught = self.refusal(self.held, fence=self.fence + 1)
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))

    def test_another_entry_under_this_lease_does_not_pass(self):
        self.place("entry-2", checkpoint_id="c-2")
        self.refusal(self.held, entry_id="entry-2")

    def test_another_target_under_this_lease_does_not_pass(self):
        activate_target(self.coordinator,
                        target(canonical_target_id="target:other",
                               description="another target"))
        self.refusal(self.held, canonical_target_id="target:other")

    def test_an_ended_lease_does_not_pass(self):
        self.integrate("entry-1", "lease-1", self.fence)
        caught = self.refusal(self.held)
        self.assertIn("released", caught.message)

    def test_a_lease_that_never_existed_does_not_pass(self):
        caught = self.refusal(self.held, lease_id="lease-9")
        self.assertIn("does not exist", caught.message)

    def test_a_blocked_target_does_not_pass_even_to_its_holder(self):
        self.block("entry-1", "lease-1", self.fence, reason="digest")
        caught = self.refusal(self.held)
        self.assertIn("not open at fence", caught.message)


class SettlementIsProvedAtBothCutpoints(QueueCase):

    def setUp(self):
        super().setUp()
        self.place("entry-1", checkpoint_id="c-1")
        self.place("entry-2", checkpoint_id="c-2")
        self.granted = self.lease("lease-1")
        self.fence = self.granted["lease"]["fence"]

    def settle(self, **replaced):
        operands = {"lease_id": "lease-1", "canonical_target_id": TARGET,
                    "fence": self.fence, "entry_id": "entry-1",
                    "settlement": SETTLEMENT}
        operands.update(replaced)
        return settle_integrated(self.coordinator, **operands)

    def test_an_integrated_entry_is_terminal_and_carries_its_account(self):
        settled = self.settle()
        self.assertEqual(settled["state"], "integrated")
        self.assertEqual(settled["settlement"], SETTLEMENT)
        self.assertIsNotNone(settled["settled_at"])

    def test_a_settlement_against_another_target_records_nothing(self):
        activate_target(self.coordinator,
                        target(canonical_target_id="target:other",
                               description="another target"))
        self.refusal(self.settle, canonical_target_id="target:other")
        self.assertEqual(self.states(), ["leased", "queued"])

    def test_a_settlement_at_a_stale_fence_records_nothing(self):
        self.refusal(self.settle, fence=self.fence + 1)
        self.assertEqual(self.states(), ["leased", "queued"])

    def test_completion_after_the_grant_ended_records_nothing(self):
        refuse_entry(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", settlement=REFUSAL,
                     lease_id="lease-1", fence=self.fence)
        caught = self.refusal(self.settle)
        self.assertIn("released", caught.message)
        self.assertEqual(self.states(), ["refused", "queued"])

    def test_the_same_entry_under_a_later_grant_is_a_collision(self):
        """Not a silent replay of the earlier import's account."""
        refuse_entry(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", settlement=REFUSAL,
                     lease_id="lease-1", fence=self.fence)
        second = self.lease("lease-2")
        caught = self.refusal(self.settle, lease_id="lease-2",
                              fence=second["lease"]["fence"])
        self.assertIn(caught.code, ("denied", "operation-collision"))

    def test_a_settlement_missing_its_verification_is_not_one(self):
        caught = self.refusal(self.settle, settlement={"imported_paths": []})
        self.assertEqual(caught.category, "integrity")

    def test_releasing_replays_and_does_not_end_a_second_time(self):
        first = self.integrate("entry-1", "lease-1", self.fence)
        again = release_lease(self.coordinator, lease_id="lease-1",
                              canonical_target_id=TARGET, entry_id="entry-1",
                              fence=self.fence, ending=INTEGRATED)
        self.assertEqual(again, first)
        self.assertEqual(again["state"], "released")

    def test_a_release_naming_another_entry_is_refused(self):
        self.settle()
        self.refusal(release_lease, self.coordinator, lease_id="lease-1",
                     canonical_target_id=TARGET, entry_id="entry-2",
                     fence=self.fence, ending=INTEGRATED)
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")

    def test_an_ending_outside_the_closed_variants_is_refused(self):
        self.settle()
        caught = self.refusal(release_lease, self.coordinator,
                              lease_id="lease-1", canonical_target_id=TARGET,
                              entry_id="entry-1", fence=self.fence,
                              ending={"outcome": "refused"})
        self.assertIn("not one of integrated, entry-refused, abandoned",
                      caught.message)
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")

    def test_an_ending_that_disagrees_with_the_entry_is_refused(self):
        """A well-formed variant that is not the one this release means."""
        self.settle()
        caught = self.refusal(release_lease, self.coordinator,
                              lease_id="lease-1", canonical_target_id=TARGET,
                              entry_id="entry-1", fence=self.fence,
                              ending={"outcome": "entry-refused"})
        self.assertIn("actually happened", caught.message)
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")


class NoLeaseEndsOverUnresolvedWork(QueueCase):
    """Review of 2026-09-06 [P0]: releasing before settlement advanced the
    queue while the prior entry still recorded unresolved canonical work.

    The suite that existed drove exactly this transition and asserted only
    that the old grant had stopped being live, which blessed the hole. These
    cases assert what must NOT have moved.
    """

    def setUp(self):
        super().setUp()
        self.place("entry-1", checkpoint_id="c-1")
        self.place("entry-2", checkpoint_id="c-2")
        self.granted = self.lease("lease-1")
        self.fence = self.granted["lease"]["fence"]

    def release(self):
        return release_lease(self.coordinator, lease_id="lease-1",
                             canonical_target_id=TARGET, entry_id="entry-1",
                             fence=self.fence, ending=INTEGRATED)

    def test_a_leased_entry_s_lease_is_not_released(self):
        caught = self.refusal(self.release)
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertIn("unaccounted for", caught.message)

    def test_the_refused_release_moved_nothing_at_all(self):
        self.refusal(self.release)
        self.assertEqual(self.states(), ["leased", "queued"])
        self.assertEqual(self.live(), ["lease-1"])
        self.assertEqual(lease_of(self.coordinator, "lease-1")["fence"],
                         self.fence)
        self.assertEqual(target_of(self.coordinator, TARGET)["fence"],
                         self.fence)

    def test_the_next_entry_is_not_offered_over_the_refused_release(self):
        self.refusal(self.release)
        self.assertIsNone(self.lease("lease-2"))
        self.assertEqual(self.states(), ["leased", "queued"])

    def test_a_held_entry_s_lease_is_not_released_either(self):
        """Refused one step earlier than the leased case, and that is right.

        A blocked target fails `live_grant` before the entry's state is
        reached, so the holder of a held entry cannot release its way out of
        a target nobody has repaired.
        """
        self.block("entry-1", "lease-1", self.fence)
        caught = self.refusal(self.release)
        self.assertIn("not open at fence", caught.message)
        self.assertEqual(self.states(), ["held", "queued"])
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")

    def test_no_public_ending_leaves_a_leased_entry_behind_a_dead_lease(self):
        """The invariant the [P0] correction is FOR, stated once.

        After the ordinary success path there is no live lease and no
        unresolved entry; after the refusal path the same; after the block
        path the lease is still live and the target refuses to offer anything.
        """
        self.integrate("entry-1", "lease-1", self.fence)
        self.assertEqual((self.states(), self.live()),
                         (["integrated", "queued"], []))
        second = self.lease("lease-2")
        refuse_entry(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-2", settlement=REFUSAL,
                     lease_id="lease-2", fence=second["lease"]["fence"])
        self.assertEqual((self.states(), self.live()),
                         (["integrated", "refused"], []))


class TheTwoRefusalsAreNotOneState(QueueCase):
    """An ordinary refusal moves the queue on; an integrity one stops it."""

    def setUp(self):
        super().setUp()
        self.place("entry-1", checkpoint_id="c-1")
        self.place("entry-2", checkpoint_id="c-2")

    def test_an_ordinary_refusal_ends_the_lease_and_offers_the_next(self):
        granted = self.lease("lease-1")
        refused = refuse_entry(self.coordinator, canonical_target_id=TARGET,
                               entry_id="entry-1", settlement=REFUSAL,
                               lease_id="lease-1",
                               fence=granted["lease"]["fence"])
        self.assertEqual(refused["state"], "refused")
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "released")
        self.assertEqual(target_of(self.coordinator, TARGET)["state"], "open")
        self.assertEqual(self.lease("lease-2")["entry"]["entry_id"], "entry-2")

    def test_a_queued_entry_is_refused_without_any_grant(self):
        refused = refuse_entry(self.coordinator, canonical_target_id=TARGET,
                               entry_id="entry-2", settlement=REFUSAL)
        self.assertEqual(refused["state"], "refused")
        self.assertEqual(self.lease("lease-1")["entry"]["entry_id"], "entry-1")

    def test_a_leased_entry_is_not_refused_by_a_caller_holding_nothing(self):
        """This verb ENDS a live lease, so it is the holder's."""
        self.lease("lease-1")
        caught = self.refusal(refuse_entry, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-1",
                              settlement=REFUSAL)
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")
        self.assertEqual(self.states(), ["leased", "queued"])

    def test_a_stale_fence_does_not_refuse_a_leased_entry(self):
        granted = self.lease("lease-1")
        self.refusal(refuse_entry, self.coordinator,
                     canonical_target_id=TARGET, entry_id="entry-1",
                     settlement=REFUSAL, lease_id="lease-1",
                     fence=granted["lease"]["fence"] + 1)
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")

    def test_a_refusal_naming_another_target_records_nothing(self):
        activate_target(self.coordinator,
                        target(canonical_target_id="target:other",
                               description="another target"))
        self.refusal(refuse_entry, self.coordinator,
                     canonical_target_id="target:other", entry_id="entry-1",
                     settlement=REFUSAL)
        self.assertEqual(self.states(), ["queued", "queued"])

    def test_a_blocked_target_holds_its_entry_and_keeps_the_lease(self):
        granted = self.lease("lease-1")
        blocked = self.block("entry-1", "lease-1", granted["lease"]["fence"],
                             reason="digest")
        self.assertEqual(blocked["entry"]["state"], "held")
        self.assertEqual(blocked["target"]["state"], "blocked")
        self.assertEqual(blocked["target"]["blocked_reason"], "digest")
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")
        self.assertEqual(granted["lease"]["fence"],
                         target_of(self.coordinator, TARGET)["fence"])

    def test_the_blocked_account_names_the_grant_that_was_live(self):
        granted = self.lease("lease-1")
        account = self.block("entry-1", "lease-1",
                             granted["lease"]["fence"])["target"][
                                 "blocked_account"]
        self.assertEqual(
            (account["entry_id"], account["lease_id"], account["fence"],
             account["attempt_id"], account["integrator_participant"]),
            ("entry-1", "lease-1", granted["lease"]["fence"], "attempt-1",
             "baton.integrator"))

    def test_a_blocked_target_offers_nothing_until_it_is_repaired(self):
        granted = self.lease("lease-1")
        self.block("entry-1", "lease-1", granted["lease"]["fence"])
        caught = self.refusal(self.lease, "lease-2")
        self.assertIn("blocked", caught.message)
        self.assertEqual(entries_of(self.coordinator, TARGET,
                                    state="queued")[0]["entry_id"], "entry-2")

    def test_blocking_stays_available_to_a_caller_holding_nothing(self):
        """Which is what keeps a crashed holder's target recoverable at all.

        The caller must NAME the live grant exactly; it need not be the
        holder. Demanding a grant here would leave one state -- a live lease
        whose holder is gone -- that nobody could ever act on.
        """
        granted = self.lease("lease-1", participant="baton.gone")
        blocked = self.block("entry-1", "lease-1", granted["lease"]["fence"])
        self.assertEqual(blocked["target"]["state"], "blocked")
        self.assertEqual(
            blocked["target"]["blocked_account"]["integrator_participant"],
            "baton.gone")

    def test_a_settled_entry_is_not_settled_again(self):
        refuse_entry(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-2", settlement=REFUSAL)
        caught = self.refusal(self.block, "entry-2", "lease-1", 1)
        self.assertIn("already refused", caught.message)


class ABlockIsAboutOneExactGrant(QueueCase):
    """Review of 2026-09-06 [P0]: the cross-wired block.

    A block naming entry B while entry A held the live lease left A `leased`,
    B `held`, and let the recovery end A's grant against B's block.
    """

    def setUp(self):
        super().setUp()
        self.place("entry-1", checkpoint_id="c-1")
        self.place("entry-2", checkpoint_id="c-2")
        self.granted = self.lease("lease-1")
        self.fence = self.granted["lease"]["fence"]
        self.recovery = {"attempt_id": "attempt-1", "evidence": "runtime gone"}

    def unchanged(self):
        self.assertEqual(self.states(), ["leased", "queued"])
        self.assertEqual(target_of(self.coordinator, TARGET)["state"], "open")
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")

    def test_another_entry_of_this_target_is_not_the_block_s_subject(self):
        caught = self.refusal(self.block, "entry-2", "lease-1", self.fence)
        self.assertIn("has no live lease", caught.message)
        self.unchanged()

    def test_another_lease_is_not_the_block_s_subject(self):
        caught = self.refusal(self.block, "entry-1", "lease-9", self.fence)
        self.assertIn("has no live lease", caught.message)
        self.unchanged()

    def test_a_stale_fence_is_not_the_block_s_subject(self):
        caught = self.refusal(self.block, "entry-1", "lease-1", self.fence + 1)
        self.assertIn("has no live lease", caught.message)
        self.unchanged()

    def test_an_entry_of_another_target_is_refused(self):
        activate_target(self.coordinator,
                        target(canonical_target_id="target:other",
                               description="another target"))
        caught = self.refusal(block_target, self.coordinator,
                              canonical_target_id="target:other",
                              entry_id="entry-1", lease_id="lease-1",
                              fence=self.fence, reason="digest", detail={})
        self.assertIn("not this target", caught.message)
        self.unchanged()

    def test_a_second_block_does_not_replace_the_recovery_s_subject(self):
        self.block("entry-1", "lease-1", self.fence)
        caught = self.refusal(self.block, "entry-2", "lease-1", self.fence)
        self.assertIn("already blocked", caught.message)
        account = target_of(self.coordinator, TARGET)["blocked_account"]
        self.assertEqual(account["entry_id"], "entry-1")
        self.assertEqual(self.states(), ["held", "queued"])

    def test_repeating_one_block_is_one_act(self):
        first = self.block("entry-1", "lease-1", self.fence)
        self.assertEqual(self.block("entry-1", "lease-1", self.fence), first)

    def test_a_recovery_ends_the_grant_the_block_was_about(self):
        self.block("entry-1", "lease-1", self.fence)
        ended = abandon_lease(self.coordinator, lease_id="lease-1",
                              fence=self.fence, recovery=self.recovery)
        self.assertEqual(ended["state"], "abandoned")
        self.assertEqual(self.states(), ["held", "queued"])

    def test_a_recovery_of_a_lease_the_block_was_not_about_is_refused(self):
        """The cross-wire, driven from the other end.

        `entry-2` is blocked under its own grant while `lease-1` is still live
        over `entry-1`; ending `lease-1` here would abandon a holder nobody
        blocked.
        """
        self.integrate("entry-1", "lease-1", self.fence)
        second = self.lease("lease-2", attempt_id="attempt-2")
        third = self.place("entry-3", checkpoint_id="c-3")
        self.block("entry-2", "lease-2", second["lease"]["fence"])
        caught = self.refusal(abandon_lease, self.coordinator,
                              lease_id="lease-2",
                              fence=second["lease"]["fence"],
                              recovery={"attempt_id": "attempt-1",
                                        "evidence": "the wrong attempt"})
        self.assertIn("accounts for", caught.message)
        self.assertEqual(lease_of(self.coordinator, "lease-2")["state"],
                         "live")
        self.assertEqual(third["rank"], 3)


class NothingExpiresAndRecoveryIsExplicit(QueueCase):

    def setUp(self):
        super().setUp()
        self.place("entry-1")
        self.granted = self.lease("lease-1", attempt_id="attempt-1")
        self.fence = self.granted["lease"]["fence"]
        self.recovery = {"attempt_id": "attempt-1",
                         "evidence": "the runtime is gone and the store agrees"}

    def test_time_alone_ends_no_lease(self):
        self.instants.append(LATER)
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")
        self.assertIsNone(self.lease("lease-2"))

    def test_a_live_lease_is_not_taken_from_an_open_target(self):
        caught = self.refusal(abandon_lease, self.coordinator,
                              lease_id="lease-1", fence=self.fence,
                              recovery=self.recovery)
        self.assertIn("is not blocked", caught.message)
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")

    def test_a_blocked_target_s_lease_is_ended_by_an_accounted_recovery(self):
        self.block("entry-1", "lease-1", self.fence)
        ended = abandon_lease(self.coordinator, lease_id="lease-1",
                              fence=self.fence, recovery=self.recovery)
        self.assertEqual(ended["state"], "abandoned")
        self.assertEqual(ended["ending"]["recovery"], self.recovery)

    def test_abandoning_does_not_reopen_the_target(self):
        self.block("entry-1", "lease-1", self.fence)
        abandon_lease(self.coordinator, lease_id="lease-1", fence=self.fence,
                      recovery=self.recovery)
        self.assertEqual(target_of(self.coordinator, TARGET)["state"],
                         "blocked")
        caught = self.refusal(self.lease, "lease-2")
        self.assertIn("blocked", caught.message)

    def test_a_recovery_accounts_for_the_attempt_the_lease_was_granted_to(self):
        self.block("entry-1", "lease-1", self.fence)
        caught = self.refusal(abandon_lease, self.coordinator,
                              lease_id="lease-1", fence=self.fence,
                              recovery={"attempt_id": "attempt-9",
                                        "evidence": "somebody else's runtime"})
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "live")

    def test_a_recovery_ends_the_grant_it_observed(self):
        self.block("entry-1", "lease-1", self.fence)
        caught = self.refusal(abandon_lease, self.coordinator,
                              lease_id="lease-1", fence=self.fence + 1,
                              recovery=self.recovery)
        self.assertIn("this recovery names", caught.message)

    def test_an_unaccounted_recovery_is_not_one(self):
        self.block("entry-1", "lease-1", self.fence)
        caught = self.refusal(abandon_lease, self.coordinator,
                              lease_id="lease-1", fence=self.fence,
                              recovery={"attempt_id": "attempt-1"})
        self.assertEqual(caught.category, "integrity")

    def test_abandoning_replays(self):
        self.block("entry-1", "lease-1", self.fence)
        first = abandon_lease(self.coordinator, lease_id="lease-1",
                              fence=self.fence, recovery=self.recovery)
        self.assertEqual(abandon_lease(self.coordinator, lease_id="lease-1",
                                       fence=self.fence,
                                       recovery=self.recovery), first)


class PersistedEvidenceIsProvedWhereItIsREAD(QueueCase):
    """Review of 2026-09-06 [P1]: redundant evidence nothing compared.

    A reader that returns corroborating-looking evidence it never checked is
    worse than one that returns none, because the corroboration is believed.
    """

    def setUp(self):
        super().setUp()
        self.place("entry-1")

    def edit(self, sql, *operands):
        self.coordinator._connection.execute(sql, operands)

    def test_an_entry_account_cannot_contradict_its_columns(self):
        """The narrow fix was to compare two copies; this is the wide one.

        There is no second copy: the account is assembled from the columns at
        the read, so the row and its account cannot name different proposals.
        The fifth review then showed that this made the disagreement
        unrepresentable without making the ROW immutable, so the same edit is
        now refused outright against the enqueue this store recorded.
        """
        self.edit("UPDATE entries SET proposal_id = 'proposal-other' "
                  "WHERE entry_id = 'entry-1'")
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertEqual(caught.category, "integrity")
        self.assertIn("recorded proposal_id 'proposal-1' and it is now "
                      "'proposal-other'", caught.message)

    def test_a_persisted_authority_is_still_an_authority_identity(self):
        self.edit("UPDATE entries SET authority_uuid = 'not-an-authority' "
                  "WHERE entry_id = 'entry-1'")
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("32 lowercase hexadecimal", caught.message)

    def test_a_target_document_about_another_target_is_refused(self):
        self.edit("UPDATE targets SET document = ? "
                  "WHERE canonical_target_id = ?",
                  '{"schema": "%s", "canonical_target_id": "target:other", '
                  '"description": "d"}' % TARGET_SCHEMA,
                  TARGET)
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertEqual(caught.category, "integrity")
        self.assertIn("one target is one identity", caught.message)

    def test_a_target_document_that_does_not_digest_is_refused(self):
        row = target_of(self.coordinator, TARGET)
        edited = dict(row["document"], description="quietly rewritten")
        import json as _json
        self.edit("UPDATE targets SET document = ? "
                  "WHERE canonical_target_id = ?",
                  _json.dumps(edited, sort_keys=True), TARGET)
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("does not digest", caught.message)

    def test_a_lease_holding_another_target_s_entry_is_refused(self):
        activate_target(self.coordinator,
                        target(canonical_target_id="target:other",
                               description="another target"))
        enqueue(self.coordinator, canonical_target_id="target:other",
                entry_id="entry-other", eligibility=eligibility(
                    checkpoint_id="c-other"))
        self.lease("lease-1")
        self.edit("UPDATE leases SET entry_id = 'entry-other' "
                  "WHERE lease_id = 'lease-1'")
        caught = self.refusal(lease_of, self.coordinator, "lease-1")
        self.assertEqual(caught.category, "integrity")
        self.assertIn("holds entry 'entry-other', which is not this target's",
                      caught.message)

    def test_a_settlement_of_the_wrong_shape_for_its_state_is_refused(self):
        granted = self.lease("lease-1")
        settle_integrated(self.coordinator, lease_id="lease-1",
                          canonical_target_id=TARGET,
                          fence=granted["lease"]["fence"],
                          entry_id="entry-1", settlement=SETTLEMENT)
        self.edit("UPDATE entries SET settlement = ? WHERE entry_id = ?",
                  '{"reason": "scope", "detail": "x"}', "entry-1")
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertEqual(caught.category, "integrity")


class TheStoreIsAdoptedByOwnershipRatherThanResemblance(CoordinatorCase):

    def opened(self, path=None, incarnation="coordinator-1"):
        return IntegrationStore.open(path or self.path,
                                     incarnation=incarnation,
                                     clock=self.clock)

    def altered(self, statement, *, path=None):
        """Build a store, close it, edit its schema behind this build's back."""
        where = path or self.path
        self.opened(where).close()
        connection = sqlite3.connect(where)
        connection.execute(statement)
        connection.commit()
        connection.close()
        return where

    def test_a_fresh_store_carries_this_build_s_kind_and_version(self):
        store = self.store()
        recorded = dict(store._connection.execute(
            "SELECT key, value FROM meta"))
        self.assertEqual(recorded["store_kind"],
                         "baton.v12.python.integration-coordinator")
        self.assertEqual(recorded["schema_version"], str(SCHEMA_VERSION))

    def test_a_foreign_database_is_refused_untouched(self):
        foreign = self.path + ".foreign"
        connection = sqlite3.connect(foreign)
        connection.execute("CREATE TABLE meta (key TEXT, value TEXT)")
        connection.execute("INSERT INTO meta VALUES ('store_kind', 'other')")
        connection.commit()
        connection.close()
        with open(foreign, "rb") as handle:
            before = handle.read()
        caught = self.refusal(self.opened, foreign)
        self.assertIn("Nothing was changed", caught.message)
        with open(foreign, "rb") as handle:
            self.assertEqual(handle.read(), before)

    def test_another_version_is_refused_rather_than_guessed_across(self):
        self.altered("UPDATE meta SET value = '99' "
                     "WHERE key = 'schema_version'")
        caught = self.refusal(self.opened, incarnation="coordinator-2")
        self.assertIn("does not guess across versions", caught.message)

    def test_the_missing_safety_index_is_not_adopted(self):
        """Review of 2026-09-06 [P1]: this reopened without complaint.

        `leases_one_live_per_target` is not an optimization; it IS the
        one-live-lease exclusion, so a store without it is a store whose
        central safety property silently is not there.
        """
        self.altered("DROP INDEX leases_one_live_per_target")
        caught = self.refusal(self.opened, incarnation="coordinator-2")
        self.assertIn("leases_one_live_per_target", caught.message)
        self.assertIn("Nothing was changed", caught.message)

    def test_an_index_whose_predicate_changed_is_not_adopted(self):
        self.altered("DROP INDEX entries_queued_by_rank")
        connection = sqlite3.connect(self.path)
        connection.execute("CREATE INDEX entries_queued_by_rank ON entries "
                           "(canonical_target_id, rank) "
                           "WHERE state = 'leased'")
        connection.commit()
        connection.close()
        caught = self.refusal(self.opened, incarnation="coordinator-2")
        self.assertIn("differently from this build", caught.message)

    def test_an_object_this_build_does_not_own_is_not_adopted(self):
        self.altered("CREATE TABLE souvenirs (note TEXT)")
        caught = self.refusal(self.opened, incarnation="coordinator-2")
        self.assertIn("souvenirs", caught.message)

    def test_metadata_this_build_does_not_own_is_not_adopted(self):
        self.altered("INSERT INTO meta (key, value) "
                     "VALUES ('owner', 'somebody else')")
        caught = self.refusal(self.opened, incarnation="coordinator-2")
        self.assertIn("owner", caught.message)

    def test_the_expectation_is_measured_from_the_schema_it_checks(self):
        """A hand-written expectation would be a second owner of the shape."""
        from baton_v12.integration.store import expected_shape
        self.assertEqual(
            {name for kind, name in expected_shape() if kind == "table"},
            {"meta", "operations", "targets", "entries", "leases"})
        self.assertIn(("index", "leases_one_live_per_target"),
                      expected_shape())


class ABlockedTargetIsONERELATIONSHIP(QueueCase):
    """Re-review of 2026-09-06 [P1]: the account was shaped, not cross-bound.

    The write transition built the relationship correctly and a RESTART
    believed a contradictory one, which is the half that matters -- the
    recovery checks against this account, so evidence that names the wrong
    grant is worse than no evidence at all.
    """

    def setUp(self):
        super().setUp()
        self.place("entry-1", checkpoint_id="c-1")
        self.place("entry-2", checkpoint_id="c-2")
        self.granted = self.lease("lease-1")
        self.fence = self.granted["lease"]["fence"]
        self.block("entry-1", "lease-1", self.fence)

    def rewrite(self, **replaced):
        """Edit the stored block account behind this build's back."""
        import json as _json
        account = dict(target_of(self.coordinator, TARGET)["blocked_account"])
        account.update(replaced)
        self.coordinator._connection.execute(
            "UPDATE targets SET blocked_account = ? "
            "WHERE canonical_target_id = ?",
            (_json.dumps(account, sort_keys=True), TARGET))

    def edit(self, sql, *operands):
        self.coordinator._connection.execute(sql, operands)

    def test_the_block_reads_back_as_the_grant_it_was_about(self):
        account = target_of(self.coordinator, TARGET)["blocked_account"]
        self.assertEqual((account["entry_id"], account["lease_id"],
                          account["fence"]), ("entry-1", "lease-1",
                                              self.fence))

    def test_an_account_naming_another_entry_is_refused(self):
        self.rewrite(entry_id="entry-2")
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertEqual(caught.category, "integrity")
        self.assertIn("rather than held", caught.message)

    def test_an_account_whose_reason_differs_from_the_row_is_refused(self):
        self.rewrite(reason="other-reason")
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("its account says", caught.message)

    def test_an_account_whose_detail_differs_from_the_entry_is_refused(self):
        self.rewrite(detail={"observed": "something else entirely"})
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("account for it differently", caught.message)

    def test_an_account_naming_another_lease_is_refused(self):
        self.rewrite(lease_id="lease-9")
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("blocked under lease 'lease-9', which is not this "
                      "target's", caught.message)

    def test_an_account_at_another_fence_is_refused(self):
        self.rewrite(fence=self.fence + 1)
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("disagree about the grant", caught.message)

    def test_an_account_naming_another_holder_is_refused(self):
        self.rewrite(attempt_id="attempt-9")
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("disagree about the grant", caught.message)

    def test_an_account_naming_another_integrator_is_refused(self):
        self.rewrite(integrator_participant="baton.someone-else")
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("disagree about the grant", caught.message)

    def test_a_blocked_target_under_a_released_lease_is_refused(self):
        self.edit("UPDATE leases SET state = 'released', ended_at = ?, "
                  "ending = ? WHERE lease_id = 'lease-1'",
                  "2026-09-06T00:00:00.000Z", '{"outcome": "integrated"}')
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("blocked under a 'released' lease", caught.message)

    def test_a_recovery_for_another_attempt_is_refused_on_read(self):
        abandon_lease(self.coordinator, lease_id="lease-1", fence=self.fence,
                      recovery={"attempt_id": "attempt-1",
                                "evidence": "the runtime is gone"})
        self.edit("UPDATE leases SET ending = ? WHERE lease_id = 'lease-1'",
                  '{"outcome": "abandoned", "recovery": '
                  '{"attempt_id": "attempt-9", "evidence": "e"}}')
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("was granted to attempt", caught.message)

    def test_a_properly_recovered_block_still_reads(self):
        abandon_lease(self.coordinator, lease_id="lease-1", fence=self.fence,
                      recovery={"attempt_id": "attempt-1",
                                "evidence": "the runtime is gone"})
        found = target_of(self.coordinator, TARGET)
        self.assertEqual(found["state"], "blocked")
        self.assertEqual(found["blocked_account"]["entry_id"], "entry-1")


class SettlementsAndEndingsAreOwnedVariants(QueueCase):
    """Re-review of 2026-09-06 [P1]: member sets were closed, shapes were not.

    Knowing WHICH members a document carries tells you nothing if you do not
    then know what they must be -- the correction `boundaries.alternative`
    already records against itself, arriving here.
    """

    def setUp(self):
        super().setUp()
        self.place("entry-1")
        self.granted = self.lease("lease-1")
        self.fence = self.granted["lease"]["fence"]

    def edit(self, sql, *operands):
        self.coordinator._connection.execute(sql, operands)

    def settle(self, settlement):
        return settle_integrated(self.coordinator, lease_id="lease-1",
                                 canonical_target_id=TARGET, fence=self.fence,
                                 entry_id="entry-1", settlement=settlement)

    def test_imported_paths_are_a_collection_of_paths(self):
        caught = self.refusal(self.settle,
                              {"imported_paths": "src/a.py",
                               "verification": {"final_bytes": "checked"}})
        self.assertIn("collection of paths", caught.message)

    def test_an_imported_path_is_durable_text(self):
        self.refusal(self.settle,
                     {"imported_paths": [7],
                      "verification": {"final_bytes": "checked"}})

    def test_a_verification_account_is_a_document(self):
        self.refusal(self.settle,
                     {"imported_paths": ["src/a.py"], "verification": "yes"})

    def test_a_refusal_reason_is_text(self):
        self.refusal(refuse_entry, self.coordinator,
                     canonical_target_id=TARGET, entry_id="entry-1",
                     settlement={"reason": 7, "detail": {}},
                     lease_id="lease-1", fence=self.fence)

    def test_a_persisted_held_reason_that_is_not_text_is_refused(self):
        self.block("entry-1", "lease-1", self.fence)
        self.edit("UPDATE entries SET settlement = ? WHERE entry_id = ?",
                  '{"reason": 7, "detail": {}}', "entry-1")
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertEqual(caught.category, "integrity")

    def test_an_abandoned_lease_does_not_end_integrated(self):
        self.block("entry-1", "lease-1", self.fence)
        abandon_lease(self.coordinator, lease_id="lease-1", fence=self.fence,
                      recovery={"attempt_id": "attempt-1",
                                "evidence": "gone"})
        self.edit("UPDATE leases SET ending = ? WHERE lease_id = 'lease-1'",
                  '{"outcome": "integrated"}')
        caught = self.refusal(lease_of, self.coordinator, "lease-1")
        self.assertIn("recorded 'abandoned', whose endings are abandoned",
                      caught.message)

    def test_a_released_lease_does_not_end_abandoned(self):
        self.integrate("entry-1", "lease-1", self.fence)
        self.edit("UPDATE leases SET ending = ? WHERE lease_id = 'lease-1'",
                  '{"outcome": "abandoned", "recovery": '
                  '{"attempt_id": "attempt-1", "evidence": "e"}}')
        caught = self.refusal(lease_of, self.coordinator, "lease-1")
        self.assertIn("recorded 'released', whose endings are integrated or "
                      "entry-refused", caught.message)

    def test_an_abandonment_without_its_recovery_is_refused(self):
        self.integrate("entry-1", "lease-1", self.fence)
        self.edit("UPDATE leases SET state = 'abandoned', ending = ? "
                  "WHERE lease_id = 'lease-1'", '{"outcome": "abandoned"}')
        caught = self.refusal(lease_of, self.coordinator, "lease-1")
        self.assertEqual(caught.category, "integrity")

    def test_a_recovery_for_another_attempt_does_not_read_back(self):
        self.integrate("entry-1", "lease-1", self.fence)
        self.edit("UPDATE leases SET state = 'abandoned', ending = ? "
                  "WHERE lease_id = 'lease-1'",
                  '{"outcome": "abandoned", "recovery": '
                  '{"attempt_id": "attempt-9", "evidence": "e"}}')
        caught = self.refusal(lease_of, self.coordinator, "lease-1")
        self.assertIn("was granted to attempt", caught.message)


class TheValueValidatedIsTheValueUsed(CoordinatorCase):
    """Re-review of 2026-09-06 [P1]: two calls signed one value and stored
    another.

    The clock is a capability this store already accepts, so it is the exact
    deterministic seam the re-review used: it fires between the validation and
    the SQL arguments. `own` snapshots every member once so that "the value we
    validated is the value we used" is a fact -- these cases prove the answer
    is not thrown away.
    """

    def setUp(self):
        super().setUp()
        self.armed = None
        self.coordinator = self.store()
        activate_target(self.coordinator, target())
        enqueue(self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-1", eligibility=eligibility())
        self.granted = grant_lease(self.coordinator,
                                   canonical_target_id=TARGET,
                                   entry_id="entry-1",
                                   lease_id="lease-1",
                                   integrator_participant="baton.integrator",
                                   attempt_id="attempt-1")
        self.fence = self.granted["lease"]["fence"]

    def clock(self):
        """This case's clock, which rewrites the caller's document once."""
        if self.armed is not None:
            document, replaced = self.armed
            document.update(replaced)
            self.armed = None
        return self.instants[-1]

    def test_a_settlement_mutated_after_validation_is_not_the_one_stored(self):
        settlement = {"imported_paths": ["reviewed.py"],
                      "verification": {"final_bytes": "checked"}}
        self.armed = (settlement, {"imported_paths": ["other.py"]})
        settled = settle_integrated(self.coordinator, lease_id="lease-1",
                                    canonical_target_id=TARGET,
                                    fence=self.fence, entry_id="entry-1",
                                    settlement=settlement)
        self.assertEqual(settled["settlement"]["imported_paths"],
                         ["reviewed.py"])
        self.assertEqual(settlement["imported_paths"], ["other.py"])

    def test_the_journalled_signature_is_the_value_that_was_validated(self):
        """So the exact retry of the reviewed value replays, rather than
        colliding with a signature nobody sent."""
        settlement = {"imported_paths": ["reviewed.py"],
                      "verification": {"final_bytes": "checked"}}
        self.armed = (settlement, {"imported_paths": ["other.py"]})
        first = settle_integrated(self.coordinator, lease_id="lease-1",
                                  canonical_target_id=TARGET,
                                  fence=self.fence, entry_id="entry-1",
                                  settlement=settlement)
        again = settle_integrated(
            self.coordinator, lease_id="lease-1", canonical_target_id=TARGET,
            fence=self.fence, entry_id="entry-1",
            settlement={"imported_paths": ["reviewed.py"],
                        "verification": {"final_bytes": "checked"}})
        self.assertEqual(again, first)
        self.assertEqual(again["settlement"]["imported_paths"],
                         ["reviewed.py"])

    def test_a_refusal_mutated_after_validation_is_not_the_one_stored(self):
        settlement = {"reason": "scope", "detail": {"path": "outside"}}
        self.armed = (settlement, {"reason": "something-else"})
        refused = refuse_entry(self.coordinator, canonical_target_id=TARGET,
                               entry_id="entry-1", settlement=settlement,
                               lease_id="lease-1", fence=self.fence)
        self.assertEqual(refused["settlement"]["reason"], "scope")
        self.assertEqual(settlement["reason"], "something-else")

    def test_a_block_account_mutated_after_validation_is_not_the_one_stored(self):
        detail = {"observed": "ambiguous custody"}
        self.armed = (detail, {"observed": "rewritten"})
        blocked = block_target(self.coordinator, canonical_target_id=TARGET,
                               entry_id="entry-1", lease_id="lease-1",
                               fence=self.fence, reason="integrity",
                               detail=detail)
        self.assertEqual(blocked["entry"]["settlement"]["detail"],
                         {"observed": "ambiguous custody"})
        self.assertEqual(
            blocked["target"]["blocked_account"]["detail"],
            {"observed": "ambiguous custody"})


class TheStateGraphIsProvedFromBothSides(QueueCase):
    """Third review of 2026-09-06 [P0]: erasing the block advanced the queue.

    The blocked relationship was validated only when the target ADMITTED to
    having one, so setting the target row back to the legal `open` shape left
    a `held` entry and an `abandoned` lease that every door accepted
    separately -- and the next grant went past unresolved held work.

    These cases read the raw rows after each refusal, because the public
    readers are exactly what must refuse.
    """

    def setUp(self):
        super().setUp()
        self.place("entry-1", checkpoint_id="c-1")
        self.place("entry-2", checkpoint_id="c-2")
        self.granted = self.lease("lease-1")
        self.fence = self.granted["lease"]["fence"]

    def edit(self, sql, *operands):
        self.coordinator._connection.execute(sql, operands)

    def erase(self):
        """The target row, back to a perfectly legal `open` shape."""
        self.edit("UPDATE targets SET state = 'open', blocked_reason = NULL, "
                  "blocked_account = NULL WHERE canonical_target_id = ?",
                  TARGET)

    def raw(self, sql, *operands):
        return [tuple(row) for row in
                self.coordinator._connection.execute(sql, operands)]

    def unmoved(self):
        """Read past the refusing doors, straight at the rows."""
        self.assertEqual(
            self.raw("SELECT entry_id, state FROM entries "
                     "WHERE canonical_target_id = ? ORDER BY rank", TARGET),
            [("entry-1", "held"), ("entry-2", "queued")])
        self.assertEqual(
            self.raw("SELECT fence FROM targets WHERE canonical_target_id = ?",
                     TARGET), [(self.fence,)])

    def every_door_refuses(self):
        self.assertEqual(self.refusal(target_of, self.coordinator,
                                      TARGET).category, "integrity")
        self.assertEqual(self.refusal(lease_of, self.coordinator,
                                      "lease-1").category, "integrity")
        self.assertEqual(self.refusal(entries_of, self.coordinator,
                                      TARGET).category, "integrity")
        self.refusal(self.lease, "lease-2")
        self.unmoved()

    def test_a_block_erased_while_its_lease_is_live_refuses_everywhere(self):
        self.block("entry-1", "lease-1", self.fence)
        self.erase()
        self.every_door_refuses()
        self.assertEqual(self.raw("SELECT state FROM leases "
                                  "WHERE lease_id = 'lease-1'"), [("live",)])

    def test_a_block_erased_after_its_recovery_refuses_everywhere(self):
        self.block("entry-1", "lease-1", self.fence)
        abandon_lease(self.coordinator, lease_id="lease-1", fence=self.fence,
                      recovery={"attempt_id": "attempt-1",
                                "evidence": "the runtime is gone"})
        self.erase()
        self.every_door_refuses()
        self.assertEqual(self.raw("SELECT state FROM leases "
                                  "WHERE lease_id = 'lease-1'"),
                         [("abandoned",)])

    def test_an_abandonment_over_an_entry_that_was_not_held_refuses(self):
        """The other half of the same erasure, on its own.

        An abandonment belongs to a held entry under a blocked target, so an
        abandoned lease over an entry recorded `refused` is refused by that
        entry's own lifecycle rather than by a rule about targets.
        """
        self.block("entry-1", "lease-1", self.fence)
        abandon_lease(self.coordinator, lease_id="lease-1", fence=self.fence,
                      recovery={"attempt_id": "attempt-1",
                                "evidence": "gone"})
        self.erase()
        self.edit("UPDATE entries SET state = 'refused' WHERE entry_id = ?",
                  "entry-1")
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("does not carry exactly the one released lease its "
                      "refusal ended", caught.message)

    def test_a_leased_entry_with_no_live_lease_refuses(self):
        """The stranded state the first review's [P0] was about, arriving
        through the store rather than through a verb."""
        self.edit("UPDATE leases SET state = 'released', ended_at = ?, "
                  "ending = ? WHERE lease_id = 'lease-1'",
                  "2026-09-06T00:00:00.000Z", '{"outcome": "integrated"}')
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("no single live lease holds it", caught.message)

    def test_a_live_lease_over_settled_work_refuses(self):
        self.edit("UPDATE entries SET state = 'refused', settled_at = ?, "
                  "settlement = ? WHERE entry_id = 'entry-1'",
                  "2026-09-06T00:00:00.000Z",
                  '{"reason": "scope", "detail": {}}')
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("does not carry exactly the one released lease its "
                      "refusal ended", caught.message)


class TheGraphDoesNotDependOnWhatThisProcessREMEMBERS(CoordinatorCase):
    """The same split state, fabricated by SQL alone.

    No verb of this package ever ran against these rows, so nothing about the
    refusal can come from operation history held in process memory -- which is
    the case a restart actually presents.
    """

    def setUp(self):
        super().setUp()
        self.coordinator = self.store()
        activate_target(self.coordinator, target())
        enqueue(self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-1", eligibility=eligibility(checkpoint_id="a"))
        enqueue(self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-2", eligibility=eligibility(checkpoint_id="b"))

    def fabricate(self, target_state="open"):
        held = '{"detail": {}, "reason": "integrity"}'
        ending = ('{"outcome": "abandoned", "recovery": '
                  '{"attempt_id": "attempt-1", "evidence": "gone"}}')
        self.coordinator._connection.execute(
            "UPDATE entries SET state = 'held', settled_at = ?, "
            "settlement = ? WHERE entry_id = 'entry-1'",
            ("2026-09-06T00:00:00.000Z", held))
        self.coordinator._connection.execute(
            "INSERT INTO leases (lease_id, canonical_target_id, entry_id, "
            "integrator_participant, attempt_id, fence, state, granted_at, "
            "ended_at, ending) VALUES ('lease-1', ?, 'entry-1', "
            "'baton.merge', 'attempt-1', 1, 'abandoned', ?, ?, ?)",
            (TARGET, "2026-09-06T00:00:00.000Z", "2026-09-06T00:00:00.000Z",
             ending))
        self.coordinator._connection.execute(
            "UPDATE targets SET fence = 1 WHERE canonical_target_id = ?",
            (TARGET,))

    def test_a_fabricated_open_target_over_held_work_refuses(self):
        self.fabricate()
        self.assertIn("held work exists only under a blocked target",
                      self.refusal(target_of, self.coordinator,
                                   TARGET).message)
        self.refusal(entries_of, self.coordinator, TARGET)
        self.refusal(lease_of, self.coordinator, "lease-1")

    def test_a_fabricated_split_state_offers_no_next_entry(self):
        self.fabricate()
        caught = self.refusal(grant_lease, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-2",
                              lease_id="lease-2",
                              integrator_participant="baton.integrator",
                              attempt_id="attempt-2")
        self.assertEqual(caught.category, "integrity")
        self.assertEqual(
            [tuple(row) for row in self.coordinator._connection.execute(
                "SELECT entry_id, state FROM entries "
                "WHERE canonical_target_id = ? ORDER BY rank", (TARGET,))],
            [("entry-1", "held"), ("entry-2", "queued")])
        self.assertEqual(
            [tuple(row) for row in self.coordinator._connection.execute(
                "SELECT lease_id FROM leases WHERE state = 'live'")], [])


class TheWholeLifecycleIsProved(CoordinatorCase):
    """Fourth review of 2026-09-06 [P0]: selected state pairs, not a lifecycle.

    Nothing checked a RELEASED lease against its entry, and nothing rejected a
    queued entry that already had a lease history -- so an integrated, released
    entry reset to its schema-valid `queued` shape passed every door and was
    leased again. An import whose durable account already says it completed,
    offered a second time.

    The matrix below is table-driven because the defect was a list somebody
    maintained: every case corrupts one relationship and asserts all four
    public doors refuse and nothing moves.
    """

    CASES = (
        ("an integrated entry reset to queued",
         [("UPDATE entries SET state = 'queued', settled_at = NULL, "
           "settlement = NULL WHERE entry_id = 'entry-1'",)]),
        ("a refused entry reset to queued",
         [("UPDATE entries SET state = 'queued', settled_at = NULL, "
           "settlement = NULL WHERE entry_id = 'entry-3'",)]),
        ("an integrated entry released as entry-refused",
         [("UPDATE leases SET ending = ? WHERE lease_id = 'lease-1'",
           '{"outcome": "entry-refused"}')]),
        ("a released lease moved onto a queued entry",
         [("UPDATE leases SET entry_id = 'entry-2' WHERE lease_id = 'lease-1'",)]),
        ("a released lease moved onto an unrelated settled entry",
         [("UPDATE leases SET entry_id = 'entry-3' WHERE lease_id = 'lease-1'",)]),
        ("an entry given a second historical lease",
         [("INSERT INTO leases (lease_id, canonical_target_id, entry_id, "
           "integrator_participant, attempt_id, fence, state, granted_at, "
           "ended_at, ending) VALUES ('lease-2', ?, 'entry-1', "
           "'baton.integrator', 'attempt-2', 2, 'released', ?, ?, ?)",
           TARGET, "2026-09-05T00:00:00.000Z", "2026-09-05T00:00:00.000Z",
           '{"outcome": "integrated"}'),
          ("UPDATE targets SET fence = 2 WHERE canonical_target_id = ?",
           TARGET)]),
        ("an entry given a live lease beside its ended one",
         [("INSERT INTO leases (lease_id, canonical_target_id, entry_id, "
           "integrator_participant, attempt_id, fence, state, granted_at) "
           "VALUES ('lease-2', ?, 'entry-1', 'baton.integrator', "
           "'attempt-2', 2, 'live', ?)",
           TARGET, "2026-09-05T00:00:00.000Z"),
          ("UPDATE targets SET fence = 2 WHERE canonical_target_id = ?",
           TARGET)]),
        ("a target fence drifted from its lease history",
         [("UPDATE targets SET fence = 5 WHERE canonical_target_id = ?",
           TARGET)]),
    )

    DOORS = ("target", "entries", "lease", "grant")

    def based(self, path):
        """One integrated-and-released entry, one queued, one refused."""
        store = self.store(path=path)
        activate_target(store, target())
        for name, checkpoint in (("entry-1", "c-1"), ("entry-2", "c-2"),
                                 ("entry-3", "c-3")):
            enqueue(store, canonical_target_id=TARGET, entry_id=name,
                    eligibility=eligibility(checkpoint_id=checkpoint))
        granted = grant_lease(store, canonical_target_id=TARGET,
                              entry_id="entry-1",
                              lease_id="lease-1",
                              integrator_participant="baton.integrator",
                              attempt_id="attempt-1")
        fence = granted["lease"]["fence"]
        settle_integrated(store, lease_id="lease-1",
                          canonical_target_id=TARGET, fence=fence,
                          entry_id="entry-1", settlement=SETTLEMENT)
        release_lease(store, lease_id="lease-1", canonical_target_id=TARGET,
                      entry_id="entry-1", fence=fence, ending=INTEGRATED)
        refuse_entry(store, canonical_target_id=TARGET, entry_id="entry-3",
                     settlement=REFUSAL)
        return store

    def knock(self, store, door):
        if door == "target":
            return target_of(store, TARGET)
        if door == "entries":
            return entries_of(store, TARGET)
        if door == "lease":
            return lease_of(store, "lease-1")
        return grant_lease(store, canonical_target_id=TARGET,
                           entry_id="entry-2",
                           lease_id="lease-9",
                           integrator_participant="baton.integrator",
                           attempt_id="attempt-9")

    def rows(self, store, sql, *operands):
        return [tuple(row) for row in store._connection.execute(sql, operands)]

    def test_every_corrupted_relationship_refuses_at_every_door(self):
        for index, (name, edits) in enumerate(self.CASES):
            for door in self.DOORS:
                with self.subTest(case=name, door=door):
                    store = self.based(f"{self.path}.{index}.{door}")
                    for edit in edits:
                        store._connection.execute(edit[0], edit[1:])
                    # SNAPSHOT THE CORRUPTED STATE, because that is what the
                    # refusal must leave alone. Comparing against the sound
                    # state would only re-measure the corruption.
                    entries = self.rows(
                        store, "SELECT entry_id, state FROM entries "
                        "WHERE canonical_target_id = ? ORDER BY rank", TARGET)
                    leases = self.rows(
                        store, "SELECT lease_id, entry_id, state, fence "
                        "FROM leases ORDER BY fence")
                    fence = self.rows(store, "SELECT fence FROM targets "
                                      "WHERE canonical_target_id = ?", TARGET)
                    caught = self.refusal(self.knock, store, door)
                    self.assertEqual(caught.category, "integrity", name)
                    self.assertEqual(
                        self.rows(store, "SELECT entry_id, state FROM entries "
                                  "WHERE canonical_target_id = ? ORDER BY rank",
                                  TARGET), entries, name)
                    self.assertEqual(
                        self.rows(store, "SELECT lease_id, entry_id, state, "
                                  "fence FROM leases ORDER BY fence"), leases,
                        name)
                    self.assertEqual(
                        self.rows(store, "SELECT fence FROM targets "
                                  "WHERE canonical_target_id = ?", TARGET),
                        fence, name)

    def test_a_held_entry_reset_to_queued_refuses(self):
        """The third terminal state, which needs a blocked base."""
        store = self.store(path=self.path + ".held")
        activate_target(store, target())
        for name, checkpoint in (("entry-1", "c-1"), ("entry-2", "c-2")):
            enqueue(store, canonical_target_id=TARGET, entry_id=name,
                    eligibility=eligibility(checkpoint_id=checkpoint))
        granted = grant_lease(store, canonical_target_id=TARGET,
                              entry_id="entry-1",
                              lease_id="lease-1",
                              integrator_participant="baton.integrator",
                              attempt_id="attempt-1")
        fence = granted["lease"]["fence"]
        block_target(store, canonical_target_id=TARGET, entry_id="entry-1",
                     lease_id="lease-1", fence=fence, reason="integrity",
                     detail={"observed": "ambiguous"})
        store._connection.execute(
            "UPDATE entries SET state = 'queued', settled_at = NULL, "
            "settlement = NULL WHERE entry_id = 'entry-1'")
        store._connection.execute(
            "UPDATE targets SET state = 'open', blocked_reason = NULL, "
            "blocked_account = NULL WHERE canonical_target_id = ?", (TARGET,))
        for door in self.DOORS:
            with self.subTest(door=door):
                self.assertEqual(
                    self.refusal(self.knock, store, door).category,
                    "integrity")

    def test_the_ordinary_lifecycle_still_reads(self):
        """The matrix would pass if everything refused, so this is the half
        that proves the rules admit a correct store."""
        store = self.based(self.path + ".sound")
        self.assertEqual([one["state"] for one in entries_of(store, TARGET)],
                         ["integrated", "queued", "refused"])
        self.assertEqual(lease_of(store, "lease-1")["state"], "released")
        self.assertEqual(target_of(store, TARGET)["fence"], 1)
        second = grant_lease(store, canonical_target_id=TARGET,
                             entry_id="entry-2",
                             lease_id="lease-2",
                             integrator_participant="baton.integrator",
                             attempt_id="attempt-2")
        self.assertEqual(second["entry"]["entry_id"], "entry-2")
        self.assertEqual(target_of(store, TARGET)["fence"], 2)


class TheJournalIsTheDurableHistory(CoordinatorCase):
    """Fifth review of 2026-09-06 [P0], twice over.

    Building operation identities from the rows that are PRESENT proves
    nothing about a row that was rewritten or deleted. An entry's immutable
    account could be edited in place -- selection then handing the integrator
    different evidence from the accepted evidence that entered the queue -- and
    a whole integration could be deleted, handing its fence back, while the
    journal that proves it happened sat untouched beside it.

    Both are provable contradictions rather than unknowable loss, which is why
    the journal is now the history the rows are proved against.
    """

    def setUp(self):
        super().setUp()
        self.coordinator = self.store()
        activate_target(self.coordinator, target())
        self.account = eligibility()
        enqueue(self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-1", eligibility=self.account)

    def edit(self, sql, *operands):
        self.coordinator._connection.execute(sql, operands)

    def rows(self, sql, *operands):
        return [tuple(row) for row in
                self.coordinator._connection.execute(sql, operands)]

    def state(self):
        """Everything durable, materialized and recorded alike."""
        return (self.rows("SELECT * FROM targets"),
                self.rows("SELECT * FROM entries"),
                self.rows("SELECT * FROM leases"),
                self.rows("SELECT * FROM operations ORDER BY operation_id"))

    def doors(self):
        return {
            "target": lambda: target_of(self.coordinator, TARGET),
            "entries": lambda: entries_of(self.coordinator, TARGET),
            "lease": lambda: lease_of(self.coordinator, "lease-1"),
            "enqueue": lambda: enqueue(
                self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-late",
                eligibility=eligibility(checkpoint_id="c-late")),
            "grant": lambda: grant_lease(
                self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-late",
                lease_id="lease-late",
                integrator_participant="baton.integrator",
                attempt_id="attempt-late"),
        }

    def every_door_refuses_and_moves_nothing(self, name, doors=None):
        for door, knock in self.doors().items():
            if doors is not None and door not in doors:
                continue
            with self.subTest(case=name, door=door):
                before = self.state()
                caught = self.refusal(knock)
                self.assertEqual(caught.category, "integrity", name)
                self.assertEqual(self.state(), before, name)

    def integrate(self):
        """One whole integration, so there is history to delete."""
        granted = grant_lease(self.coordinator, canonical_target_id=TARGET,
                              entry_id="entry-1",
                              lease_id="lease-1",
                              integrator_participant="baton.integrator",
                              attempt_id="attempt-1")
        fence = granted["lease"]["fence"]
        settle_integrated(self.coordinator, lease_id="lease-1",
                          canonical_target_id=TARGET, fence=fence,
                          entry_id="entry-1", settlement=SETTLEMENT)
        release_lease(self.coordinator, lease_id="lease-1",
                      canonical_target_id=TARGET, entry_id="entry-1",
                      fence=fence, ending=INTEGRATED)
        return fence

    # -- the account is immutable ------------------------------------------

    def test_every_operand_of_the_account_is_immutable(self):
        """The whole account, member by member, not the two the review named."""
        # THE ACCOUNT'S OWN MEMBERS, not a list beside it. W101714's review
        # found this matrix naming a member the account no longer had, which is
        # what a second copy of a member set is for.
        from baton_v12.integration.queue import ELIGIBILITY_MEMBERS
        for name in ELIGIBILITY_MEMBERS:
            with self.subTest(operand=name):
                case = self.store(path=f"{self.path}.{name}")
                activate_target(case, target())
                enqueue(case, canonical_target_id=TARGET, entry_id="entry-1",
                        eligibility=eligibility())
                rewritten = (2 if name == "assignment_generation"
                             else "rewritten")
                case._connection.execute(
                    f"UPDATE entries SET {name} = ? WHERE entry_id = ?",
                    (rewritten, "entry-1"))
                if name == "authority_uuid":
                    # Refused one step earlier, by the identity rule.
                    self.assertEqual(
                        self.refusal(entries_of, case, TARGET).category,
                        "integrity")
                    continue
                caught = self.refusal(entries_of, case, TARGET)
                self.assertIn(f"recorded {name}", caught.message)

    def test_a_reassigned_rank_is_refused(self):
        self.edit("UPDATE entries SET rank = 7 WHERE entry_id = 'entry-1'")
        # No lease was ever granted here, so `lease_of` truthfully answers
        # that there is none; the other four doors must refuse.
        self.every_door_refuses_and_moves_nothing(
            "rank reassigned", ("target", "entries", "enqueue", "grant"))

    def test_an_entry_moved_to_another_target_is_refused(self):
        activate_target(self.coordinator,
                        target(canonical_target_id="target:other",
                               description="another target"))
        self.edit("UPDATE entries SET canonical_target_id = 'target:other' "
                  "WHERE entry_id = 'entry-1'")
        caught = self.refusal(entries_of, self.coordinator, "target:other")
        self.assertEqual(caught.category, "integrity")
        self.assertIn("recorded no enqueue of it here", caught.message)
        # And the target it was recorded against notices it has gone.
        self.assertIn("no such entry is materialized",
                      self.refusal(entries_of, self.coordinator,
                                   TARGET).message)

    # -- deleted history ----------------------------------------------------

    def test_a_deleted_queued_entry_is_refused(self):
        self.edit("DELETE FROM entries WHERE entry_id = 'entry-1'")
        self.every_door_refuses_and_moves_nothing(
            "queued entry deleted", ("target", "entries", "enqueue", "grant"))

    def test_a_deleted_integration_is_refused_at_every_door(self):
        """The review's exact scenario: rows gone, journal intact."""
        self.integrate()
        self.edit("DELETE FROM leases WHERE lease_id = 'lease-1'")
        self.edit("DELETE FROM entries WHERE entry_id = 'entry-1'")
        self.edit("UPDATE targets SET fence = 0 "
                  "WHERE canonical_target_id = ?", TARGET)
        self.every_door_refuses_and_moves_nothing("integration deleted")

    def test_a_deleted_live_lease_is_refused(self):
        grant_lease(self.coordinator, canonical_target_id=TARGET,
                    entry_id="entry-1",
                    lease_id="lease-1",
                    integrator_participant="baton.integrator",
                    attempt_id="attempt-1")
        self.edit("DELETE FROM leases WHERE lease_id = 'lease-1'")
        self.edit("UPDATE entries SET state = 'queued' "
                  "WHERE entry_id = 'entry-1'")
        self.every_door_refuses_and_moves_nothing("live lease deleted")

    def test_a_deleted_target_row_is_refused(self):
        self.edit("DELETE FROM entries WHERE entry_id = 'entry-1'")
        self.edit("DELETE FROM targets WHERE canonical_target_id = ?", TARGET)
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("recorded the activation of target", caught.message)

    def test_a_fence_below_its_durable_history_is_refused(self):
        """Where the fence rule earns its keep: the rows are sound and only
        the counter has been wound back."""
        self.integrate()
        self.edit("UPDATE targets SET fence = 0 "
                  "WHERE canonical_target_id = ?", TARGET)
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("the greatest fence in its durable history is 1",
                      caught.message)

    def test_the_original_checkpoint_is_not_admitted_a_second_time(self):
        self.integrate()
        self.edit("DELETE FROM leases WHERE lease_id = 'lease-1'")
        self.edit("DELETE FROM entries WHERE entry_id = 'entry-1'")
        before = self.state()
        caught = self.refusal(enqueue, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-2",
                              eligibility=self.account)
        self.assertEqual(caught.category, "integrity")
        self.assertEqual(self.state(), before)

    # -- the journal itself is evidence, so it is adopted -------------------

    def test_a_record_signed_as_another_kind_is_refused(self):
        self.edit("UPDATE operations SET signature = ? "
                  "WHERE operation_id = 'entry.enqueue:entry-1'",
                  '{"kind": "lease.grant", "operands": {}}')
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("recorded 'entry.enqueue' and signed 'lease.grant'",
                      caught.message)

    def test_a_record_of_a_kind_this_build_does_not_own_is_refused(self):
        self.edit("INSERT INTO operations (seq, operation_id, kind, "
                  "signature, state, result, settled_at) VALUES "
                  "(?, 'x', 'entry.forget', ?, 'committed', 'null', ?)",
                  self.next_position(self.coordinator),
                  '{"kind": "entry.forget", "operands": {}}',
                  "2026-09-06T00:00:00.000Z")
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("which this build does not own", caught.message)

    def test_a_record_whose_operands_are_short_is_refused(self):
        self.edit("UPDATE operations SET signature = ? "
                  "WHERE operation_id = 'entry.enqueue:entry-1'",
                  '{"kind": "entry.enqueue", "operands": '
                  '{"canonical_target_id": "target:mainline"}}')
        self.assertEqual(
            self.refusal(entries_of, self.coordinator, TARGET).category,
            "integrity")

    def test_a_record_whose_result_lost_a_member_is_refused(self):
        self.edit("UPDATE operations SET result = ? "
                  "WHERE operation_id = 'entry.enqueue:entry-1'",
                  '{"entry_id": "entry-1"}')
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("needs canonical_target_id", caught.message)

    def test_a_signature_that_does_not_decode_is_refused(self):
        self.edit("UPDATE operations SET signature = 'not json' "
                  "WHERE operation_id = 'entry.enqueue:entry-1'")
        self.assertEqual(
            self.refusal(entries_of, self.coordinator, TARGET).category,
            "integrity")

    # -- the window inside a transaction is exactly one act ----------------

    def test_no_act_is_pending_outside_a_transaction(self):
        self.assertIsNone(self.coordinator._pending)

    def test_a_pending_act_excuses_only_itself(self):
        """The window is keyed to one operation identity, not to "some act is
        running" -- which would readmit every fabricated row."""
        self.edit("INSERT INTO entries (entry_id, canonical_target_id, rank, "
                  "authority_uuid, work_id, assignment_generation, line_id, "
                  "checkpoint_id, verdict_id, checkpoint_digest, proposal_id, "
                  "candidate_digest, result_id, result_digest, profile_kind, "
                  "expected_target_revision, path_set_digest, scope_digest, "
                  "state, enqueued_at) SELECT 'entry-ghost', "
                  "canonical_target_id, 9, authority_uuid, work_id, "
                  "assignment_generation, line_id, 'c-ghost', verdict_id, "
                  "checkpoint_digest, proposal_id, candidate_digest, "
                  "result_id, result_digest, profile_kind, "
                  "expected_target_revision, "
                  "path_set_digest, scope_digest, 'queued', enqueued_at "
                  "FROM entries WHERE entry_id = 'entry-1'")
        before = self.state()
        caught = self.refusal(enqueue, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-new",
                              eligibility=eligibility(checkpoint_id="c-new"))
        self.assertIn("entry 'entry-ghost' is materialized on target "
                      "'target:mainline' and this store recorded no enqueue "
                      "of it here", caught.message)
        self.assertEqual(self.state(), before)

    # -- and the sound store still works ------------------------------------

    def test_the_ordinary_history_reads_and_replays(self):
        fence = self.integrate()
        self.assertEqual(entries_of(self.coordinator, TARGET)[0]["state"],
                         "integrated")
        self.assertEqual(lease_of(self.coordinator, "lease-1")["state"],
                         "released")
        self.assertEqual(target_of(self.coordinator, TARGET)["fence"], fence)
        # Exact replays return the FIRST outcome, which is what makes them
        # replays: the activation's result is the target as it was adopted.
        self.assertEqual(activate_target(self.coordinator, target())["fence"],
                         0)
        self.assertEqual(enqueue(self.coordinator, canonical_target_id=TARGET,
                                 entry_id="entry-1",
                                 eligibility=self.account)["rank"], 1)

    def test_a_reopened_store_proves_the_same_history(self):
        self.integrate()
        again = self.store(incarnation="coordinator-2")
        self.assertEqual([one["state"] for one in entries_of(again, TARGET)],
                         ["integrated"])
        self.assertEqual(target_of(again, TARGET)["state"], "open")


class EveryRecordedActIsProvedWhole(CoordinatorCase):
    """Sixth review of 2026-09-06.

    [P0] The signed request was never compared to its own result, so rewriting
    BOTH redundant surfaces -- the materialized row and the journalled result
    -- left two agreeing witnesses and a signed request that contradicted them,
    and selection believed the two. The signed request is the one thing a
    rewrite cannot reach without changing what was accepted.

    [P1] The operand contract closed the key set and typed nothing, and a
    committed row with a SQL NULL result escaped as a raw `TypeError`.
    """

    SETTLED = ("target.activate", "entry.enqueue", "lease.grant",
               "entry.integrated", "lease.release", "entry.refuse")
    BLOCKED = ("target.block", "lease.abandon")

    def settled(self, path):
        """Activate, enqueue two, integrate one, refuse the other."""
        store = self.store(path=path)
        activate_target(store, target())
        for name, checkpoint in (("entry-1", "c-1"), ("entry-2", "c-2")):
            enqueue(store, canonical_target_id=TARGET, entry_id=name,
                    eligibility=eligibility(checkpoint_id=checkpoint))
        granted = grant_lease(store, canonical_target_id=TARGET,
                              entry_id="entry-1",
                              lease_id="lease-1",
                              integrator_participant="baton.integrator",
                              attempt_id="attempt-1")
        fence = granted["lease"]["fence"]
        settle_integrated(store, lease_id="lease-1",
                          canonical_target_id=TARGET, fence=fence,
                          entry_id="entry-1", settlement=SETTLEMENT)
        release_lease(store, lease_id="lease-1", canonical_target_id=TARGET,
                      entry_id="entry-1", fence=fence, ending=INTEGRATED)
        refuse_entry(store, canonical_target_id=TARGET, entry_id="entry-2",
                     settlement=REFUSAL)
        return store

    def blocked(self, path):
        """Activate, enqueue one, block it, recover the holder."""
        store = self.store(path=path)
        activate_target(store, target())
        enqueue(store, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=eligibility())
        granted = grant_lease(store, canonical_target_id=TARGET,
                              entry_id="entry-1",
                              lease_id="lease-1",
                              integrator_participant="baton.integrator",
                              attempt_id="attempt-1")
        fence = granted["lease"]["fence"]
        block_target(store, canonical_target_id=TARGET, entry_id="entry-1",
                     lease_id="lease-1", fence=fence, reason="integrity",
                     detail={"observed": "ambiguous"})
        abandon_lease(store, lease_id="lease-1", fence=fence,
                      recovery={"attempt_id": "attempt-1",
                                "evidence": "the runtime is gone"})
        return store

    def based(self, kind, path):
        return (self.blocked(path) if kind in self.BLOCKED
                else self.settled(path))

    def named(self, store, kind):
        """This kind's one operation id in the base it belongs to."""
        for row in store._connection.execute(
                "SELECT operation_id FROM operations WHERE kind = ?", (kind,)):
            return row["operation_id"]
        raise AssertionError(kind)

    def rewrite(self, store, operation_id, column, mutate):
        import json as _json
        row = store._connection.execute(
            f"SELECT {column} FROM operations WHERE operation_id = ?",
            (operation_id,)).fetchone()
        value = _json.loads(row[column])
        mutate(value)
        store._connection.execute(
            f"UPDATE operations SET {column} = ? WHERE operation_id = ?",
            (_json.dumps(value, sort_keys=True), operation_id))

    def durable(self, store):
        return [[tuple(row) for row in store._connection.execute(sql)]
                for sql in ("SELECT * FROM targets", "SELECT * FROM entries",
                            "SELECT * FROM leases",
                            "SELECT * FROM operations ORDER BY operation_id")]

    def refuses_unchanged(self, store, why):
        before = self.durable(store)
        for door, knock in (("target", lambda: target_of(store, TARGET)),
                            ("entries", lambda: entries_of(store, TARGET))):
            with self.subTest(case=why, door=door):
                caught = self.refusal(knock)
                self.assertEqual(caught.category, "integrity", why)
        self.assertEqual(self.durable(store), before, why)

    # -- the signed operands are typed, not merely present ------------------

    ILL_TYPED = {
        "target.activate": lambda o: o["target"].update(description=7),
        "entry.enqueue": lambda o: o["eligibility"].update(candidate_digest=7),
        "lease.grant": lambda o: o.update(attempt_id=7),
        "entry.integrated": lambda o: o["settlement"].update(
            verification="not a document"),
        "entry.refuse": lambda o: o["settlement"].update(reason=7),
        "lease.release": lambda o: o["ending"].update(outcome="nonsense"),
        "target.block": lambda o: o["account"].update(reason=7),
        "lease.abandon": lambda o: o["recovery"].update(evidence=7),
    }

    def test_an_ill_typed_signed_operand_is_refused_for_every_kind(self):
        for kind, mutate in self.ILL_TYPED.items():
            with self.subTest(kind=kind):
                store = self.based(kind, f"{self.path}.typed.{kind}")
                self.rewrite(store, self.named(store, kind), "signature",
                             lambda value: mutate(value["operands"]))
                self.refuses_unchanged(store, f"ill-typed {kind}")

    # -- the signed request and its own result must agree -------------------

    MISMATCHED = {
        "entry.enqueue": lambda o: o["eligibility"].update(
            checkpoint_id="checkpoint-rewritten"),
        "lease.grant": lambda o: o.update(
            integrator_participant="baton.someone-else"),
        "entry.integrated": lambda o: o["settlement"].update(
            imported_paths=["other.py"]),
        "entry.refuse": lambda o: o["settlement"].update(detail={"other": 1}),
        "lease.release": lambda o: o.update(fence=9),
        "target.block": lambda o: o.update(fence=9),
        "lease.abandon": lambda o: o["recovery"].update(evidence="different"),
    }

    def test_a_result_that_is_not_its_request_s_is_refused(self):
        """`target.activate` is absent on purpose: its identity is derived
        from the document, so changing the document changes which act it is
        rather than making one act disagree with itself."""
        for kind, mutate in self.MISMATCHED.items():
            with self.subTest(kind=kind):
                store = self.based(kind, f"{self.path}.bound.{kind}")
                self.rewrite(store, self.named(store, kind), "signature",
                             lambda value: mutate(value["operands"]))
                self.refuses_unchanged(store, f"mismatched {kind}")

    def test_the_row_and_the_result_together_do_not_outvote_the_request(self):
        """The review's [P0]: both redundant surfaces rewritten to agree."""
        store = self.settled(self.path + ".both")
        self.rewrite(store, "entry.enqueue:entry-2", "result",
                     lambda value: value.update(
                         checkpoint_id="checkpoint-rewritten",
                         candidate_digest="sha256:rewritten"))
        store._connection.execute(
            "UPDATE entries SET checkpoint_id = 'checkpoint-rewritten', "
            "candidate_digest = 'sha256:rewritten' WHERE entry_id = 'entry-2'")
        self.refuses_unchanged(store, "row and result rewritten together")
        # And the original candidate is still not admissible a second time.
        self.assertEqual(
            self.refusal(enqueue, store, canonical_target_id=TARGET,
                         entry_id="entry-3",
                         eligibility=eligibility(checkpoint_id="c-2")
                         ).category, "integrity")

    # -- identities are derived, results are variants -----------------------

    def test_a_noncanonical_operation_id_is_refused(self):
        store = self.settled(self.path + ".id")
        store._connection.execute(
            "UPDATE operations SET operation_id = 'entry.enqueue:entry-9' "
            "WHERE operation_id = 'entry.enqueue:entry-1'")
        caught = self.refusal(target_of, store, TARGET)
        self.assertIn("an identity is derived from what was asked",
                      caught.message)

    def test_two_activations_of_one_target_are_refused(self):
        store = self.settled(self.path + ".twice")
        import json as _json
        document = dict(target(), description="a second description")
        operands = {"target": document}
        store._connection.execute(
            "INSERT INTO operations (seq, operation_id, kind, signature, "
            "state, result, settled_at) VALUES (?, ?, 'target.activate', ?, "
            "'committed', ?, ?)",
            (self.next_position(store),
             self.activation_id(document), _json.dumps(
                {"kind": "target.activate", "operands": operands},
                sort_keys=True),
             _json.dumps({"canonical_target_id": TARGET,
                          "document": document,
                          "digest": self.digest_of(document),
                          "state": "open", "fence": 0,
                          "blocked_reason": None, "blocked_account": None,
                          "activated_at": "2026-09-06T00:00:00.000Z"},
                         sort_keys=True),
             "2026-09-06T00:00:00.000Z"))
        caught = self.refusal(target_of, store, TARGET)
        self.assertIn("two committed target.activate acts", caught.message)

    def activation_id(self, document):
        from baton_v12.integration.queue import _activation_operation
        return _activation_operation(document)

    def digest_of(self, document):
        from baton_v12.contracts import digest
        return digest(document)

    def test_a_committed_act_with_a_sql_null_result_is_refused(self):
        store = self.settled(self.path + ".null")
        store._connection.execute(
            "UPDATE operations SET result = NULL "
            "WHERE operation_id = 'entry.enqueue:entry-1'")
        caught = self.refusal(target_of, store, TARGET)
        self.assertIn("records no result at all", caught.message)

    def test_a_result_of_the_wrong_variant_is_refused(self):
        store = self.settled(self.path + ".variant")
        store._connection.execute(
            "UPDATE operations SET result = 'null' "
            "WHERE operation_id = 'entry.enqueue:entry-1'")
        caught = self.refusal(target_of, store, TARGET)
        self.assertIn("records no result", caught.message)

    def test_a_grant_over_an_empty_queue_records_a_typed_empty_result(self):
        """The one kind whose result may legitimately be absent."""
        store = self.store(path=self.path + ".empty")
        activate_target(store, target())
        self.assertIsNone(grant_lease(
            store, canonical_target_id=TARGET, entry_id="entry-1",
            lease_id="lease-1",
            integrator_participant="baton.integrator",
            attempt_id="attempt-1"))
        self.assertEqual(target_of(store, TARGET)["fence"], 0)
        self.assertEqual(entries_of(store, TARGET), [])

    # -- the pending act is bound too ---------------------------------------

    def test_a_pending_act_must_have_asked_for_the_row_it_wrote(self):
        """Its identity is provenance a caller chooses; its operands are not.

        A ghost row carrying the id the pending enqueue is about is refused
        because the account it holds is not the account being enqueued.
        """
        store = self.store(path=self.path + ".pending")
        activate_target(store, target())
        enqueue(store, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=eligibility())
        store._connection.execute(
            "INSERT INTO entries (entry_id, canonical_target_id, rank, "
            "authority_uuid, work_id, assignment_generation, line_id, "
            "checkpoint_id, verdict_id, checkpoint_digest, proposal_id, "
            "candidate_digest, result_id, result_digest, profile_kind, "
            "expected_target_revision, path_set_digest, scope_digest, "
            "state, enqueued_at) SELECT 'entry-ghost', canonical_target_id, "
            "9, authority_uuid, work_id, assignment_generation, line_id, "
            "'c-ghost', verdict_id, checkpoint_digest, proposal_id, "
            "candidate_digest, result_id, result_digest, profile_kind, "
            "expected_target_revision, path_set_digest, scope_digest, "
            "'queued', enqueued_at FROM entries WHERE entry_id = 'entry-1'")
        before = self.durable(store)
        caught = self.refusal(enqueue, store, canonical_target_id=TARGET,
                              entry_id="entry-ghost",
                              eligibility=eligibility(checkpoint_id="c-new"))
        self.assertIn("recorded checkpoint_id", caught.message)
        self.assertEqual(self.durable(store), before)

    # -- and the sound store still works ------------------------------------

    def test_a_complete_history_reads_replays_and_reopens(self):
        store = self.settled(self.path + ".sound")
        self.assertEqual([one["state"] for one in entries_of(store, TARGET)],
                         ["integrated", "refused"])
        self.assertEqual(lease_of(store, "lease-1")["state"], "released")
        self.assertEqual(activate_target(store, target())["fence"], 0)
        self.assertEqual(enqueue(store, canonical_target_id=TARGET,
                                 entry_id="entry-1",
                                 eligibility=eligibility(
                                     checkpoint_id="c-1"))["rank"], 1)
        again = self.store(incarnation="coordinator-2",
                           path=self.path + ".sound")
        self.assertEqual(target_of(again, TARGET)["fence"], 1)

    def test_a_blocked_history_reads_and_reopens(self):
        store = self.blocked(self.path + ".sound-blocked")
        found = target_of(store, TARGET)
        self.assertEqual(found["state"], "blocked")
        self.assertEqual(found["blocked_account"]["lease_id"], "lease-1")
        self.assertEqual(lease_of(store, "lease-1")["state"], "abandoned")


class EveryRetryIsPROVEDBeforeItIsAnswered(CoordinatorCase):
    """Seventh review of 2026-09-06 [P0].

    `IntegrationStore.replay` read one row, compared the caller's raw signature
    text and handed back `json.loads(result)`. So the operand contract, the
    derived identity, the result variant and the whole materialized
    relationship were reached by ordinary reads and by first executions and by
    NOTHING ELSE -- and the retry path, which exists to make a transition
    effectively once, was the one door in this module that believed the journal
    without reading it.

    The two consequences the review demonstrated are the first two cases here:
    a rewritten enqueue result replayed as the caller's own candidate, and a
    fabricated committed `entry.integrated` replayed as a successful
    post-import cutpoint while its entry was still `leased` and its settlement
    had never happened. The second crosses the boundary this store exists for.
    """

    SETTLED = ("target.activate", "entry.enqueue", "lease.grant",
               "entry.integrated", "lease.release", "entry.refuse")
    BLOCKED = ("target.block", "lease.abandon")

    def settled(self, path):
        store = self.store(path=path)
        activate_target(store, target())
        for name, checkpoint in (("entry-1", "c-1"), ("entry-2", "c-2")):
            enqueue(store, canonical_target_id=TARGET, entry_id=name,
                    eligibility=eligibility(checkpoint_id=checkpoint))
        grant_lease(store, canonical_target_id=TARGET, entry_id="entry-1",
                    lease_id="lease-1",
                    integrator_participant="baton.integrator",
                    attempt_id="attempt-1")
        settle_integrated(store, lease_id="lease-1",
                          canonical_target_id=TARGET, fence=1,
                          entry_id="entry-1", settlement=SETTLEMENT)
        release_lease(store, lease_id="lease-1", canonical_target_id=TARGET,
                      entry_id="entry-1", fence=1, ending=INTEGRATED)
        refuse_entry(store, canonical_target_id=TARGET, entry_id="entry-2",
                     settlement=REFUSAL)
        return store

    def blocked(self, path):
        store = self.store(path=path)
        activate_target(store, target())
        enqueue(store, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=eligibility())
        grant_lease(store, canonical_target_id=TARGET, entry_id="entry-1",
                    lease_id="lease-1",
                    integrator_participant="baton.integrator",
                    attempt_id="attempt-1")
        block_target(store, canonical_target_id=TARGET, entry_id="entry-1",
                     lease_id="lease-1", fence=1, reason="integrity",
                     detail={"observed": "ambiguous"})
        abandon_lease(store, lease_id="lease-1", fence=1,
                      recovery={"attempt_id": "attempt-1",
                                "evidence": "the runtime is gone"})
        return store

    def based(self, kind, path):
        return (self.blocked(path) if kind in self.BLOCKED
                else self.settled(path))

    def again(self, store, kind):
        """The EXACT call that made this act, made a second time."""
        return {
            "target.activate": lambda: activate_target(store, target()),
            "entry.enqueue": lambda: enqueue(
                store, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=eligibility(checkpoint_id="c-1")),
            "lease.grant": lambda: grant_lease(
                store, canonical_target_id=TARGET, entry_id="entry-1",
                lease_id="lease-1",
                integrator_participant="baton.integrator",
                attempt_id="attempt-1"),
            "entry.integrated": lambda: settle_integrated(
                store, lease_id="lease-1", canonical_target_id=TARGET,
                fence=1, entry_id="entry-1", settlement=SETTLEMENT),
            "lease.release": lambda: release_lease(
                store, lease_id="lease-1", canonical_target_id=TARGET,
                entry_id="entry-1", fence=1, ending=INTEGRATED),
            "entry.refuse": lambda: refuse_entry(
                store, canonical_target_id=TARGET, entry_id="entry-2",
                settlement=REFUSAL),
            "target.block": lambda: block_target(
                store, canonical_target_id=TARGET, entry_id="entry-1",
                lease_id="lease-1", fence=1, reason="integrity",
                detail={"observed": "ambiguous"}),
            "lease.abandon": lambda: abandon_lease(
                store, lease_id="lease-1", fence=1,
                recovery={"attempt_id": "attempt-1",
                          "evidence": "the runtime is gone"}),
        }[kind]

    def named(self, store, kind):
        for row in store._connection.execute(
                "SELECT operation_id FROM operations WHERE kind = ?", (kind,)):
            return row["operation_id"]
        raise AssertionError(kind)

    def rewrite(self, store, operation_id, column, mutate):
        import json as _json
        row = store._connection.execute(
            f"SELECT {column} FROM operations WHERE operation_id = ?",
            (operation_id,)).fetchone()
        value = _json.loads(row[column])
        mutate(value)
        store._connection.execute(
            f"UPDATE operations SET {column} = ? WHERE operation_id = ?",
            (_json.dumps(value, sort_keys=True), operation_id))

    def durable(self, store):
        return [[tuple(row) for row in store._connection.execute(sql)]
                for sql in ("SELECT * FROM targets", "SELECT * FROM entries",
                            "SELECT * FROM leases",
                            "SELECT * FROM operations ORDER BY seq")]

    # -- a corrupted first outcome is not handed to its retry ---------------

    CORRUPT = {
        "target.activate": lambda r: r.update(digest="sha256:rewritten"),
        "entry.enqueue": lambda r: r.update(
            candidate_digest="sha256:rewritten"),
        "lease.grant": lambda r: r["lease"].update(
            integrator_participant="somebody.else"),
        "entry.integrated": lambda r: r["settlement"]["imported_paths"].append(
            "src/never-reviewed.py"),
        "lease.release": lambda r: r.update(state="abandoned"),
        "entry.refuse": lambda r: r["settlement"].update(reason="rewritten"),
        "target.block": lambda r: r["entry"].update(state="queued"),
        "lease.abandon": lambda r: r["ending"]["recovery"].update(
            evidence="rewritten"),
    }

    def test_a_corrupted_result_is_refused_on_retry_for_every_kind(self):
        """Every operation family, because a retry is every verb's first act."""
        for kind, mutate in self.CORRUPT.items():
            with self.subTest(kind=kind):
                store = self.based(kind, f"{self.path}.retry.{kind}")
                self.rewrite(store, self.named(store, kind), "result", mutate)
                before = self.durable(store)
                caught = self.refusal(self.again(store, kind))
                self.assertEqual(caught.category, "integrity", kind)
                self.assertEqual(self.durable(store), before, kind)

    def test_the_reviewer_s_rewritten_candidate_does_not_replay(self):
        """The review's first reproduction, at the door it entered by.

        `enqueue` reaches the journal before it reads anything, so this is the
        retry path and nothing else answering.
        """
        store = self.store(path=self.path + ".candidate")
        activate_target(store, target())
        account = eligibility()
        enqueue(store, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=account)
        self.rewrite(store, "entry.enqueue:entry-1", "result",
                     lambda result: result.update(
                         candidate_digest="sha256:rewritten"))
        caught = self.refusal(enqueue, store, canonical_target_id=TARGET,
                              entry_id="entry-1", eligibility=account)
        self.assertIn("sha256:rewritten", caught.message)
        self.assertEqual(
            store._connection.execute(
                "SELECT candidate_digest FROM entries").fetchone()[0],
            account["candidate_digest"])

    def test_a_fabricated_settlement_does_not_replay_as_success(self):
        """The review's second reproduction, and the one that crosses the
        boundary this store exists for.

        `settle_integrated` is the post-import cutpoint: its success is what
        lets Authority completion follow. A committed act carrying the exact
        settlement signature and a fabricated result made it answer success
        over an entry that was still `leased` and had settled nothing.
        """
        import json as _json
        store = self.store(path=self.path + ".fabricated")
        activate_target(store, target())
        enqueue(store, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=eligibility())
        granted = grant_lease(store, canonical_target_id=TARGET,
                              entry_id="entry-1",
                              lease_id="lease-1",
                              integrator_participant="baton.integrator",
                              attempt_id="attempt-1")
        fence = granted["lease"]["fence"]
        operands = {"entry_id": "entry-1", "lease_id": "lease-1",
                    "canonical_target_id": TARGET, "fence": fence,
                    "settlement": SETTLEMENT}
        forged = dict(granted["entry"], state="integrated", settled_at=NOW,
                      settlement=SETTLEMENT)
        store._connection.execute(
            "INSERT INTO operations (seq, operation_id, kind, signature, "
            "state, result, settled_at) VALUES (?, ?, 'entry.integrated', ?, "
            "'committed', ?, ?)",
            (self.next_position(store), "entry.integrated:entry-1",
             integration_signature("entry.integrated", operands),
             _json.dumps(forged, sort_keys=True), NOW))
        before = self.durable(store)
        caught = self.refusal(settle_integrated, store, lease_id="lease-1",
                              canonical_target_id=TARGET, fence=fence,
                              entry_id="entry-1", settlement=SETTLEMENT)
        self.assertIn("rather than 'integrated'", caught.message)
        self.assertEqual(self.durable(store), before)

    def test_a_retry_meets_a_row_that_no_longer_matches_its_result(self):
        """The mismatch is between the row and the first outcome, so only the
        retry is standing where it can be seen."""
        store = self.store(path=self.path + ".mismatch")
        activate_target(store, target())
        account = eligibility()
        enqueue(store, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=account)
        store._connection.execute(
            "UPDATE entries SET work_id = '0000000a-W9' "
            "WHERE entry_id = 'entry-1'")
        before = self.durable(store)
        caught = self.refusal(enqueue, store, canonical_target_id=TARGET,
                              entry_id="entry-1", eligibility=account)
        self.assertEqual(caught.category, "integrity")
        self.assertEqual(self.durable(store), before)

    def test_a_committed_retry_with_a_sql_null_result_is_refused(self):
        store = self.store(path=self.path + ".null")
        activate_target(store, target())
        account = eligibility()
        enqueue(store, canonical_target_id=TARGET, entry_id="entry-1",
                eligibility=account)
        store._connection.execute(
            "UPDATE operations SET result = NULL "
            "WHERE operation_id = 'entry.enqueue:entry-1'")
        caught = self.refusal(enqueue, store, canonical_target_id=TARGET,
                              entry_id="entry-1", eligibility=account)
        self.assertIn("records no result at all", caught.message)

    def test_a_malformed_sealed_refusal_is_refused_rather_than_revived(self):
        """A refused act replays as the refusal it was; a refusal this build
        cannot place is not one of them."""
        import json as _json
        store = self.store(path=self.path + ".malformed")
        activate_target(store, target())
        account = eligibility()
        signature = integration_signature(
            "entry.enqueue", {"canonical_target_id": TARGET,
                              "entry_id": "entry-1", "eligibility": account})
        store._connection.execute(
            "INSERT INTO operations (seq, operation_id, kind, signature, "
            "state, refusal, settled_at) VALUES (?, 'entry.enqueue:entry-1', "
            "'entry.enqueue', ?, 'refused', ?, ?)",
            (self.next_position(store), signature,
             _json.dumps({"category": 7, "code": "denied", "message": "no",
                          "durable": True}, sort_keys=True), NOW))
        caught = self.refusal(enqueue, store, canonical_target_id=TARGET,
                              entry_id="entry-1", eligibility=account)
        self.assertEqual(caught.category, "integrity")

    def test_a_well_formed_refusal_still_replays_as_itself(self):
        """The other half: adopting the refusal is not refusing it."""
        import json as _json
        store = self.store(path=self.path + ".sealed")
        activate_target(store, target())
        account = eligibility()
        signature = integration_signature(
            "entry.enqueue", {"canonical_target_id": TARGET,
                              "entry_id": "entry-1", "eligibility": account})
        store._connection.execute(
            "INSERT INTO operations (seq, operation_id, kind, signature, "
            "state, refusal, settled_at) VALUES (?, 'entry.enqueue:entry-1', "
            "'entry.enqueue', ?, 'refused', ?, ?)",
            (self.next_position(store), signature,
             _json.dumps({"category": "policy", "code": "denied",
                          "message": "the first attempt already decided this",
                          "durable": True}, sort_keys=True), NOW))
        caught = self.refusal(enqueue, store, canonical_target_id=TARGET,
                              entry_id="entry-1", eligibility=account)
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertIn("already decided this", caught.message)

    # -- and a sound retry still returns the FIRST outcome ------------------

    def test_a_sound_retry_returns_the_first_outcome_for_every_kind(self):
        """Which is what makes it a replay, and what a proof must not cost."""
        for kind in self.SETTLED + self.BLOCKED:
            with self.subTest(kind=kind):
                store = self.based(kind, f"{self.path}.sound.{kind}")
                before = self.durable(store)
                replayed = self.again(store, kind)()
                self.assertEqual(self.durable(store), before, kind)
                self.assertEqual(replayed, self.again(store, kind)(), kind)
        self.assertEqual(replayed["state"], "abandoned")


class TheORDERIsTheWitnessForWhatWasGENERATED(CoordinatorCase):
    """Seventh review of 2026-09-06's second [P0].

    A generated decision has no request-side witness and cannot have one:
    `enqueue` cannot sign the rank it is about to allocate and `grant_lease`
    cannot sign the fence it is about to burn. So rank, fence and selection had
    exactly two witnesses -- the recorded result and the materialized row --
    and the review rewrote BOTH, moving entry 1 behind entry 2 and watching
    selection follow the reversed queue. The signed enqueue was present and
    true throughout; it simply never said anything about rank.

    `operations.seq` is the third witness, and it is a different KIND of one:
    not a value about the decision, but the position the act holds among every
    act this store committed. The Nth enqueue allocated rank N, the Nth grant
    that took a lease burned fence N, and replaying the enqueues and
    settlements before a grant says which entry it could have taken.

    THE LIMIT IS STATED RATHER THAN IMPLIED. There is no durable secret here to
    sign an order with, so a writer who also rewrites `seq` presents a
    self-consistent alternative history this seam cannot distinguish from the
    real one. What these cases prove is the exact claim: a rewrite of the
    result and the row now contradicts a surface neither of them touches.
    """

    def setUp(self):
        super().setUp()
        self.coordinator = self.store()
        activate_target(self.coordinator, target())
        for name, checkpoint in (("entry-1", "c-1"), ("entry-2", "c-2")):
            enqueue(self.coordinator, canonical_target_id=TARGET,
                    entry_id=name, eligibility=eligibility(
                        checkpoint_id=checkpoint))

    def edit(self, sql, *operands):
        self.coordinator._connection.execute(sql, operands)

    def rewrite(self, operation_id, mutate):
        import json as _json
        row = self.coordinator._connection.execute(
            "SELECT result FROM operations WHERE operation_id = ?",
            (operation_id,)).fetchone()
        value = _json.loads(row["result"])
        mutate(value)
        self.edit("UPDATE operations SET result = ? WHERE operation_id = ?",
                  _json.dumps(value, sort_keys=True), operation_id)

    def durable(self):
        return [[tuple(row) for row in self.coordinator._connection.execute(sql)]
                for sql in ("SELECT * FROM targets", "SELECT * FROM entries",
                            "SELECT * FROM leases",
                            "SELECT * FROM operations ORDER BY seq")]

    def every_door_refuses_and_moves_nothing(self, why):
        doors = {
            "target": lambda: target_of(self.coordinator, TARGET),
            "entries": lambda: entries_of(self.coordinator, TARGET),
            "enqueue": lambda: enqueue(
                self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-late",
                eligibility=eligibility(checkpoint_id="c-late")),
            "grant": lambda: grant_lease(
                self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-late",
                lease_id="lease-late",
                integrator_participant="baton.integrator",
                attempt_id="attempt-late"),
        }
        before = self.durable()
        for door, knock in doors.items():
            with self.subTest(case=why, door=door):
                caught = self.refusal(knock)
                self.assertEqual(caught.category, "integrity", why)
        self.assertEqual(self.durable(), before, why)

    def entry_document(self, entry_id, **changed):
        """One entry as a recorded result carries it: the row plus its
        account."""
        from baton_v12.integration.queue import ELIGIBILITY_MEMBERS
        row = self.coordinator._connection.execute(
            "SELECT * FROM entries WHERE entry_id = ?", (entry_id,)).fetchone()
        document = {key: row[key] for key in row.keys()}
        document["eligibility"] = {name: document[name]
                                   for name in ELIGIBILITY_MEMBERS}
        document.update(changed)
        return document

    # -- the review's reproduction ------------------------------------------

    def test_a_coordinated_rank_rewrite_reverses_nothing(self):
        """Both surfaces rewritten, exactly as the review drove it."""
        self.edit("UPDATE entries SET rank = 3 WHERE entry_id = 'entry-1'")
        self.rewrite("entry.enqueue:entry-1",
                     lambda result: result.update(rank=3))
        self.every_door_refuses_and_moves_nothing("rank rewritten in both")

    def test_the_reversed_queue_is_named_in_the_refusal(self):
        self.edit("UPDATE entries SET rank = 3 WHERE entry_id = 'entry-1'")
        self.rewrite("entry.enqueue:entry-1",
                     lambda result: result.update(rank=3))
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("is enqueue number 1", caught.message)
        self.assertIn("recorded rank 3", caught.message)

    # -- selection is the order's to decide too -----------------------------

    def test_a_grant_retargeted_past_a_lower_queued_rank_is_refused(self):
        """The same rewrite one level up: the lease row and the grant result
        agree that the second entry was taken, and rank 1 was still queued."""
        grant_lease(self.coordinator, canonical_target_id=TARGET,
                    entry_id="entry-1",
                    lease_id="lease-1",
                    integrator_participant="baton.integrator",
                    attempt_id="attempt-1")
        self.edit("UPDATE entries SET state = 'queued' "
                  "WHERE entry_id = 'entry-1'")
        self.edit("UPDATE entries SET state = 'leased' "
                  "WHERE entry_id = 'entry-2'")
        self.edit("UPDATE leases SET entry_id = 'entry-2' "
                  "WHERE lease_id = 'lease-1'")
        retargeted = self.entry_document("entry-2")
        self.rewrite("lease.grant:lease-1",
                     lambda result: (result["lease"].update(
                         entry_id="entry-2"),
                         result.update(entry=retargeted)))
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("is not the result of the grant that was signed",
                      caught.message)

    def test_a_grant_that_recorded_nothing_while_work_was_queued_is_refused(self):
        """The typed empty result is a CLAIM about the queue, not a shrug."""
        grant_lease(self.coordinator, canonical_target_id=TARGET,
                    entry_id="entry-1",
                    lease_id="lease-1",
                    integrator_participant="baton.integrator",
                    attempt_id="attempt-1")
        self.edit("DELETE FROM leases WHERE lease_id = 'lease-1'")
        self.edit("UPDATE entries SET state = 'queued' "
                  "WHERE entry_id = 'entry-1'")
        self.edit("UPDATE targets SET fence = 0 WHERE canonical_target_id = ?",
                  TARGET)
        self.edit("UPDATE operations SET result = 'null' "
                  "WHERE operation_id = 'lease.grant:lease-1'")
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("records no result", caught.message)

    # -- the fence is a generated decision as well --------------------------

    def test_a_coordinated_fence_rewrite_is_refused(self):
        """Result, lease row and target counter all moved together."""
        grant_lease(self.coordinator, canonical_target_id=TARGET,
                    entry_id="entry-1",
                    lease_id="lease-1",
                    integrator_participant="baton.integrator",
                    attempt_id="attempt-1")
        refuse_entry(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", settlement=REFUSAL,
                     lease_id="lease-1", fence=1)
        grant_lease(self.coordinator, canonical_target_id=TARGET,
                    entry_id="entry-2",
                    lease_id="lease-2",
                    integrator_participant="baton.integrator",
                    attempt_id="attempt-2")
        self.edit("UPDATE leases SET fence = 5 WHERE lease_id = 'lease-2'")
        self.edit("UPDATE targets SET fence = 5 WHERE canonical_target_id = ?",
                  TARGET)
        self.rewrite("lease.grant:lease-2",
                     lambda result: result["lease"].update(fence=5))
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("grant number 2 and burned fence 5", caught.message)

    # -- and the order itself is proved dense -------------------------------

    def test_a_journal_position_that_leaves_a_hole_is_refused(self):
        self.edit("UPDATE operations SET seq = seq + 5 "
                  "WHERE operation_id = 'entry.enqueue:entry-2'")
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("the order acts committed in is dense from one",
                      caught.message)

    def test_reordering_the_journal_contradicts_the_results_it_reorders(self):
        """The honest limit, driven rather than asserted: rewriting the third
        surface does not buy agreement, it moves the disagreement."""
        self.edit("UPDATE operations SET seq = 99 "
                  "WHERE operation_id = 'entry.enqueue:entry-1'")
        self.edit("UPDATE operations SET seq = 2 "
                  "WHERE operation_id = 'entry.enqueue:entry-2'")
        self.edit("UPDATE operations SET seq = 3 "
                  "WHERE operation_id = 'entry.enqueue:entry-1'")
        caught = self.refusal(entries_of, self.coordinator, TARGET)
        self.assertIn("entry 'entry-2' is enqueue number 1", caught.message)
        self.assertIn("recorded rank 2", caught.message)

    def test_a_duplicate_or_missing_rank_is_unrepresentable(self):
        """Not caught -- excluded, by `UNIQUE (canonical_target_id, rank)` and
        by `NOT NULL`. The schema is where a state that must never exist
        belongs."""
        self.assertRaises(
            sqlite3.IntegrityError, self.edit,
            "UPDATE entries SET rank = 1 WHERE entry_id = 'entry-2'")
        self.assertRaises(
            sqlite3.IntegrityError, self.edit,
            "UPDATE entries SET rank = NULL WHERE entry_id = 'entry-2'")

    # -- the positive half --------------------------------------------------

    def test_a_long_mixed_history_still_reads_and_still_orders(self):
        """The matrix above would pass if everything refused."""
        enqueue(self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-3", eligibility=eligibility(
                    authority_uuid=UUID_B, checkpoint_id="c-3"))
        # Refuse the head before it is ever offered, so selection must skip it.
        refuse_entry(self.coordinator, canonical_target_id=TARGET,
                     entry_id="entry-1", settlement=REFUSAL)
        first = grant_lease(self.coordinator, canonical_target_id=TARGET,
                            entry_id="entry-2",
                            lease_id="lease-1",
                            integrator_participant="baton.integrator",
                            attempt_id="attempt-1")
        self.assertEqual(first["entry"]["entry_id"], "entry-2")
        self.assertEqual(first["lease"]["fence"], 1)
        settle_integrated(self.coordinator, lease_id="lease-1",
                          canonical_target_id=TARGET, fence=1,
                          entry_id="entry-2", settlement=SETTLEMENT)
        release_lease(self.coordinator, lease_id="lease-1",
                      canonical_target_id=TARGET, entry_id="entry-2",
                      fence=1, ending=INTEGRATED)
        second = grant_lease(self.coordinator, canonical_target_id=TARGET,
                             entry_id="entry-3",
                             lease_id="lease-2",
                             integrator_participant="baton.integrator",
                             attempt_id="attempt-2")
        self.assertEqual(second["entry"]["entry_id"], "entry-3")
        self.assertEqual(second["lease"]["fence"], 2)
        self.assertEqual([(one["entry_id"], one["rank"], one["state"])
                          for one in entries_of(self.coordinator, TARGET)],
                         [("entry-1", 1, "refused"),
                          ("entry-2", 2, "integrated"),
                          ("entry-3", 3, "leased")])
        # And the exact replays still return their first outcomes.
        self.assertEqual(grant_lease(
            self.coordinator, canonical_target_id=TARGET, entry_id="entry-3",
            lease_id="lease-2",
            integrator_participant="baton.integrator",
            attempt_id="attempt-2"), second)
        self.assertEqual(enqueue(self.coordinator, canonical_target_id=TARGET,
                                 entry_id="entry-3",
                                 eligibility=eligibility(
                                     authority_uuid=UUID_B,
                                     checkpoint_id="c-3"))["rank"], 3)

    def test_a_reopened_store_derives_the_same_order(self):
        again = self.store(incarnation="coordinator-2")
        self.assertEqual([one["rank"] for one in entries_of(again, TARGET)],
                         [1, 2])


class TheCoordinatorVocabularyIsVCSNEUTRAL(QueueCase):
    """The owner clarifications of 2026-09-06, driven rather than asserted.

    Core Baton mechanically owns serialized target admission, the live fenced
    grant, exclusive target write access, quiescence and durable settlement. It
    does not parse or validate commits, refs, branches, trees, ancestry or
    merges, and v12 does not require a VCS-aware adapter to exist at all. The
    eligibility account carried `base_object`, `head_object`, `tree_object` and
    `transport_ref` and the target document carried a `checkout`: five version
    control operands sitting inside coordinator vocabulary.

    A GATE RATHER THAN A COMMENT, because the way that vocabulary arrived the
    first time is that each operand looked locally reasonable. The first case
    below fails the moment one of those nouns is added back to a column or a
    member, whatever the prose beside it says.
    """

    # Prose may explain what was removed and why -- these are IDENTIFIERS, and
    # a name is what a schema means.
    VCS_NOUNS = frozenset((
        "commit", "commits", "ref", "refs", "branch", "branches",
        "tree", "trees", "blob", "blobs", "tag", "tags", "object", "objects",
        "checkout", "clone", "merge", "rebase", "ancestry", "parent",
        "transport", "sha1", "packfile", "worktree"))

    def vocabulary(self):
        """Every name this build's own schema and documents spell."""
        from baton_v12.integration import queue as owned
        names = set()
        for columns in (schema.TARGET_COLUMNS, schema.ENTRY_COLUMNS,
                        schema.LEASE_COLUMNS, schema.OPERATION_COLUMNS):
            names.update(columns)
        names.update(owned.TARGET_MEMBERS)
        names.update(owned.ELIGIBILITY_MEMBERS)
        names.update(owned.BLOCK_MEMBERS)
        names.update(owned.RECOVERY_MEMBERS)
        for members in owned.SETTLEMENT_MEMBERS.values():
            names.update(members)
        for required, optional in owned.ENDING_VARIANTS.values():
            names.update(required)
            names.update(optional)
        return names

    def test_no_core_name_is_a_version_control_noun(self):
        found = sorted(name for name in self.vocabulary()
                       if set(name.split("_")) & self.VCS_NOUNS)
        self.assertEqual(found, [],
                         "coordinator vocabulary naming a version control "
                         "concept")

    def test_the_target_document_is_a_name_and_not_a_location(self):
        from baton_v12.integration import queue as owned
        self.assertEqual(owned.TARGET_MEMBERS,
                         ("schema", "canonical_target_id", "description"))
        self.assertNotIn("checkout",
                         target_of(self.coordinator, TARGET)["document"])

    # -- and the profile boundary is closed rather than opaque --------------

    def test_a_member_without_a_producer_cannot_return_through_the_account(self):
        """The clarification refuses an opaque document by name, so the
        account stays closed: an operand this build does not own is refused
        rather than carried."""
        caught = self.refusal(
            enqueue, self.coordinator, canonical_target_id=TARGET,
            entry_id="entry-1",
            eligibility=eligibility(proposal_manifest_digest="sha256:x"))
        self.assertEqual(caught.category, "integrity")
        self.assertEqual(entries_of(self.coordinator, TARGET), [])

    def test_a_git_operand_cannot_return_through_the_account_either(self):
        caught = self.refusal(
            enqueue, self.coordinator, canonical_target_id=TARGET,
            entry_id="entry-1",
            eligibility=eligibility(base_object="a" * 40))
        self.assertEqual(caught.category, "integrity")
        self.assertEqual(entries_of(self.coordinator, TARGET), [])

    def test_the_account_is_typed_member_by_member(self):
        for name, value in (("profile_kind", 7),
                            ("profile_kind", None),
                            # Zero passed `boundaries.generation`, which counts
                            # from zero, and reached the column's own `>= 1`
                            # CHECK as a raw `IntegrityError`.
                            ("assignment_generation", 0),
                            ("assignment_generation", "1"),
                            ("scope_digest", None)):
            with self.subTest(member=name, value=value):
                caught = self.refusal(
                    enqueue, self.coordinator, canonical_target_id=TARGET,
                    entry_id="entry-1",
                    eligibility=eligibility(**{name: value}))
                self.assertEqual(caught.category, "integrity")
        self.assertEqual(entries_of(self.coordinator, TARGET), [])

    def test_a_missing_member_never_reaches_the_queue(self):
        account = eligibility()
        del account["profile_kind"]
        caught = self.refusal(enqueue, self.coordinator,
                              canonical_target_id=TARGET, entry_id="entry-1",
                              eligibility=account)
        self.assertIn("profile_kind", caught.message)



class OneProofObservesOneSnapshot(CoordinatorCase):
    """Eighth review of 2026-09-06's first [P1].

    The witness the seventh round added was semantically complete and
    transactionally incoherent. `_relationship` read the target row, then the
    entries, then the leases, then the whole journal, each in its own
    autocommit statement -- so an ordinary grant committing between two of them
    left the pass holding a composite that never existed, and it reported that
    as corruption. The worst possible answer: nothing was corrupt, the schedule
    was the one this store exists to serialize, and the caller was an exact
    retry that owed its first outcome.

    THE CASE IS DETERMINISTIC RATHER THAN THREADED. It fires the interleaving
    grant from inside `_target_row`, which is exactly the boundary the review
    named, so there is no timing to be lucky about.
    """

    def setUp(self):
        super().setUp()
        self.reader = self.store(incarnation="reader")
        self.writer = self.store(incarnation="writer")
        activate_target(self.reader, target())
        self.first = enqueue(self.reader, canonical_target_id=TARGET,
                             entry_id="entry-1",
                             eligibility=eligibility(checkpoint_id="c-1"))
        self.second = enqueue(self.reader, canonical_target_id=TARGET,
                              entry_id="entry-2",
                              eligibility=eligibility(checkpoint_id="c-2"))

    def interleaving(self, act):
        """Commit `act` on the writer the first time the reader reads a target
        row, and put the real `_target_row` back afterwards."""
        from baton_v12.integration import queue as owned
        original = owned._target_row
        state = {"fired": False}

        def once(store, canonical_target_id):
            value = original(store, canonical_target_id)
            if store is self.reader and not state["fired"]:
                state["fired"] = True
                act()
            return value

        owned._target_row = once
        self.addCleanup(setattr, owned, "_target_row", original)
        return state

    def grant(self):
        return grant_lease(self.writer, canonical_target_id=TARGET,
                           entry_id="entry-1",
                           lease_id="lease-1",
                           integrator_participant="baton.integrator",
                           attempt_id="attempt-1")

    def test_a_sound_retry_across_a_concurrent_grant_returns_its_first_outcome(self):
        state = self.interleaving(self.grant)
        replayed = enqueue(self.reader, canonical_target_id=TARGET,
                           entry_id="entry-2",
                           eligibility=eligibility(checkpoint_id="c-2"))
        self.assertTrue(state["fired"])
        self.assertEqual(replayed, self.second)
        self.assertEqual(replayed["rank"], 2)

    def test_the_interleaved_grant_really_committed(self):
        """Otherwise this class would prove coherence by proving nothing
        happened."""
        state = self.interleaving(self.grant)
        enqueue(self.reader, canonical_target_id=TARGET, entry_id="entry-2",
                eligibility=eligibility(checkpoint_id="c-2"))
        self.assertTrue(state["fired"])
        held = lease_of(self.reader, "lease-1")
        self.assertEqual((held["state"], held["fence"], held["entry_id"]),
                         ("live", 1, "entry-1"))
        self.assertEqual(target_of(self.reader, TARGET)["fence"], 1)
        self.assertEqual([one["state"] for one in
                          entries_of(self.reader, TARGET)],
                         ["leased", "queued"])

    def test_an_ordinary_read_across_a_concurrent_grant_is_coherent_too(self):
        """The same defect at the other door: a read is a proof as well."""
        self.interleaving(self.grant)
        found = entries_of(self.reader, TARGET)
        self.assertEqual([(one["entry_id"], one["rank"]) for one in found],
                         [("entry-1", 1), ("entry-2", 2)])

    def test_the_store_asks_for_wal_so_a_reader_does_not_block_a_writer(self):
        """Stated as its own case so an exotic filesystem is DIAGNOSED here.

        Coherence does not depend on the journal mode -- the read transaction
        is the proof, and it holds either way. What WAL decides is whether the
        two cases above are an interleaving or a five-second lock timeout, so
        a store that could not get it would fail this one case with a plain
        answer instead of failing those two mysteriously.
        """
        self.assertEqual(
            self.reader._connection.execute(
                "PRAGMA journal_mode").fetchone()[0], "wal")

    def test_the_wal_switch_is_a_request_and_a_busy_answer_is_not_one(self):
        """The claim that WAL is requested and not required, driven.

        Switching the journal mode needs the file to itself, and
        `PRAGMA journal_mode` is one of the statements that can answer BUSY
        without the busy handler retrying it -- so two coordinators opening one
        store at the same instant can meet it. A correct store with a narrower
        concurrency story is the right outcome there; a raw
        `sqlite3.OperationalError` out of a public constructor is not.

        MEASURED RATHER THAN ANTICIPATED: the sibling `ControlStore` performs
        this switch inside `_initialize` and a parallel suite raced it exactly
        there, which is what sent me looking at my own.
        """
        from baton_v12.integration.store import IntegrationStore
        place = self.path + ".busy"
        opener = sqlite3.connect(place, isolation_level=None)
        self.addCleanup(opener.close)
        opener.execute("PRAGMA journal_mode = DELETE")
        opener.execute("CREATE TABLE keep (x INTEGER)")
        blocker = sqlite3.connect(place, isolation_level=None, timeout=0)
        self.addCleanup(blocker.close)
        blocker.execute("BEGIN IMMEDIATE")
        blocker.execute("INSERT INTO keep VALUES (1)")
        self.assertEqual(IntegrationStore._concurrent(opener, place),
                         "delete")

    def test_the_snapshot_yields_to_a_transaction_already_held(self):
        """Inside `transact` the write transaction IS the observation, and
        opening a second one would be an error rather than a guarantee."""
        connection = self.reader._connection
        self.assertFalse(connection.in_transaction)
        with self.reader.snapshot():
            self.assertTrue(connection.in_transaction)
            with self.reader.snapshot():
                self.assertTrue(connection.in_transaction)
            # The inner one owned nothing, so it ended nothing.
            self.assertTrue(connection.in_transaction)
        self.assertFalse(connection.in_transaction)

    def test_a_refusal_inside_a_snapshot_does_not_strand_the_connection(self):
        self.reader._connection.execute(
            "UPDATE entries SET rank = 7 WHERE entry_id = 'entry-1'")
        self.refusal(entries_of, self.reader, TARGET)
        self.assertFalse(self.reader._connection.in_transaction)


class RefusedActsAreEvidenceToo(CoordinatorCase):
    """Eighth review of 2026-09-06's second [P1].

    `replay` branched on `state == "refused"` and revived the sealed refusal
    before the witness ran, and `_history` skipped a refused row the moment its
    generic columns and its position had been checked. So "every retry is
    proved" and "a kind this build does not own refuses the read" were true of
    committed rows and of nothing else: an exact refused retry answered its
    policy refusal over a journal with a hole in it, and a schema-valid refused
    row of a kind this build cannot reason about sat in a sound target while
    every door answered normally.

    A refused act changed nothing, which is what makes it a refusal. What it
    SAYS is still evidence: which act was asked for, under which operands, at
    which position, with which sealed outcome.
    """

    SEALED = {"category": "policy", "code": "denied", "durable": True,
              "message": "the first attempt already decided this"}

    def setUp(self):
        super().setUp()
        self.coordinator = self.store()
        activate_target(self.coordinator, target())
        self.account = eligibility(checkpoint_id="c-1")
        enqueue(self.coordinator, canonical_target_id=TARGET,
                entry_id="entry-1", eligibility=self.account)
        self.refused_account = eligibility(checkpoint_id="c-2")
        self.refused_signature = integration_signature(
            "entry.enqueue", {"canonical_target_id": TARGET,
                              "entry_id": "entry-2",
                              "eligibility": self.refused_account})

    def edit(self, sql, *operands):
        self.coordinator._connection.execute(sql, operands)

    def record_refusal(self, operation_id, kind, signature, sealed=None):
        import json as _json
        self.edit(
            "INSERT INTO operations (seq, operation_id, kind, signature, "
            "state, refusal, settled_at) VALUES (?, ?, ?, ?, 'refused', ?, ?)",
            self.next_position(self.coordinator), operation_id, kind,
            signature,
            _json.dumps(self.SEALED if sealed is None else sealed,
                        sort_keys=True),
            NOW)

    def retry(self):
        return enqueue(self.coordinator, canonical_target_id=TARGET,
                       entry_id="entry-2", eligibility=self.refused_account)

    def both_doors_refuse(self, why):
        for door, knock in (("read", lambda: target_of(self.coordinator,
                                                       TARGET)),
                            ("refused-retry", self.retry)):
            with self.subTest(case=why, door=door):
                caught = self.refusal(knock)
                self.assertEqual(caught.category, "integrity", why)

    # -- the control: a sound journal replays the refusal it recorded --------

    def test_a_refused_act_over_a_sound_journal_replays_as_its_refusal(self):
        self.record_refusal("entry.enqueue:entry-2", "entry.enqueue",
                            self.refused_signature)
        caught = self.refusal(self.retry)
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))
        self.assertIn("already decided this", caught.message)
        # And it stays a refusal rather than becoming an entry.
        self.assertEqual([one["entry_id"] for one in
                          entries_of(self.coordinator, TARGET)], ["entry-1"])

    # -- but it is proved first ---------------------------------------------

    def test_a_journal_hole_is_found_before_the_refusal_is_replayed(self):
        """The review's exact reproduction: the refused retry answered its
        policy refusal while the very next ordinary read found the hole."""
        self.record_refusal("entry.enqueue:entry-2", "entry.enqueue",
                            self.refused_signature)
        self.edit("DELETE FROM operations "
                  "WHERE operation_id = 'entry.enqueue:entry-1'")
        self.both_doors_refuse("journal hole under a refused retry")
        caught = self.refusal(self.retry)
        self.assertIn("dense from one", caught.message)

    def test_a_kind_this_build_does_not_own_refuses_both_doors(self):
        self.record_refusal("unknown:1", "unknown.kind", "{}")
        self.both_doors_refuse("a refused act of an unknown kind")
        self.assertIn("which this build does not own",
                      self.refusal(target_of, self.coordinator,
                                   TARGET).message)

    def test_an_ill_typed_signed_operand_refuses_both_doors(self):
        import json as _json
        account = dict(self.refused_account, candidate_digest=7)
        self.record_refusal(
            "entry.enqueue:entry-3", "entry.enqueue",
            _json.dumps({"kind": "entry.enqueue",
                         "operands": {"canonical_target_id": TARGET,
                                      "entry_id": "entry-3",
                                      "eligibility": account}},
                        sort_keys=True))
        self.both_doors_refuse("a refused act with an ill-typed operand")

    def test_a_noncanonical_refused_identity_is_refused_on_read(self):
        """Not reachable from a retry -- a caller derives the id it presents,
        so this door is the ordinary read's."""
        self.record_refusal("entry.enqueue:entry-9", "entry.enqueue",
                            self.refused_signature)
        caught = self.refusal(target_of, self.coordinator, TARGET)
        self.assertIn("an identity is derived from what was asked",
                      caught.message)

    def test_a_corrupted_committed_act_is_found_under_a_refused_retry(self):
        """The refused act itself is sound; what it must not do is answer over
        a journal that is not."""
        import json as _json
        self.record_refusal("entry.enqueue:entry-2", "entry.enqueue",
                            self.refused_signature)
        row = self.coordinator._connection.execute(
            "SELECT result FROM operations "
            "WHERE operation_id = 'entry.enqueue:entry-1'").fetchone()
        rewritten = _json.loads(row["result"])
        rewritten["candidate_digest"] = "sha256:rewritten"
        self.edit("UPDATE operations SET result = ? "
                  "WHERE operation_id = 'entry.enqueue:entry-1'",
                  _json.dumps(rewritten, sort_keys=True))
        self.both_doors_refuse("a rewritten committed act beside a refusal")

    def test_a_refused_act_moves_nothing_when_it_is_refused(self):
        self.record_refusal("unknown:1", "unknown.kind", "{}")
        before = [[tuple(row) for row in
                   self.coordinator._connection.execute(sql)]
                  for sql in ("SELECT * FROM targets", "SELECT * FROM entries",
                              "SELECT * FROM leases",
                              "SELECT * FROM operations ORDER BY seq")]
        self.refusal(self.retry)
        self.refusal(target_of, self.coordinator, TARGET)
        self.assertEqual(
            [[tuple(row) for row in self.coordinator._connection.execute(sql)]
             for sql in ("SELECT * FROM targets", "SELECT * FROM entries",
                         "SELECT * FROM leases",
                         "SELECT * FROM operations ORDER BY seq")],
            before)


class EveryMemberOfTheAccountHasAProducer(QueueCase):
    """W101491's finding and W101714's review, kept as a gate.

    THE RULE: a member of an immutable evidence account needs a NAMED,
    ACCEPTED PRODUCER before it is minted. The test is not "can this build
    validate its type" -- `profile_version`, `profile_account_digest` and
    `proposal_manifest_digest` were all typed, closed, cross-bound to the
    journal and proved against the signed act, and all three were still
    unprovable -- but "which accepted act computed it, and how does a later
    reader recompute it from that act".

    WHY THIS IS A MAP AND NOT A COUNT. The first version of this case asserted
    that two names were absent and the tuple was fourteen long, and it passed
    while its own title was false: `proposal_manifest_digest` was still there
    with no producer anywhere in the accepted Python surface. Counting members
    cannot find a member without a producer. Naming the surface and asking that
    surface whether it offers the name can, and does it for every member rather
    than for the ones somebody remembered.
    """

    # WHERE EACH MEMBER COMES FROM, and every surface here is read from the
    # producing package rather than transcribed.
    PRODUCERS = {
        "authority_uuid": "attempt-assignment",
        "work_id": "attempt-assignment",
        "assignment_generation": "attempt-assignment",
        "line_id": "checkpoint-verdict",
        "checkpoint_id": "checkpoint-verdict",
        "verdict_id": "checkpoint-verdict",
        "checkpoint_digest": "checkpoint-verdict",
        "path_set_digest": "checkpoint-verdict",
        "proposal_id": "authority-proposal",
        "candidate_digest": "authority-proposal",
        "result_id": "authority-proposal",
        "result_digest": "authority-proposal",
        "expected_target_revision": "authority-proposal",
        "profile_kind": "checkpoint-evidence-profile",
        "scope_digest": "accepted-job",
    }

    def surfaces(self):
        """What each accepted producer actually offers, asked of it directly."""
        import sqlite3 as engine
        from baton_v12.authority import schema as authority
        from baton_v12.job_manager import schema as jobs
        from baton_v12.worker_manager import attempts
        from baton_v12.worker_manager import schema as manager
        scratch = engine.connect(":memory:")
        self.addCleanup(scratch.close)
        scratch.executescript(authority.SCHEMA)
        proposal = {row[1] for row in
                    scratch.execute("PRAGMA table_info(proposal)")}
        # The account's own name for the proposal's target revision; the
        # Authority calls the column `target`, and naming that here is the
        # cross-binding rather than hiding it.
        proposal.add("expected_target_revision" if "target" in proposal
                     else "")
        # THE CHECKPOINT EVIDENCE'S OWN CLOSED MEMBER SET, read from the
        # accepted column contract rather than manufactured. W101714's second
        # review: this used to be the set literal `{"profile_kind"}`, so the
        # assertion below was true of nothing -- it would have kept passing if
        # the accepted evidence dropped `profile` entirely, which is exactly
        # the producer question being asked.
        #
        # The account RENAMES the member, and naming the rename here is the
        # cross-binding rather than hiding it: the evidence carries `profile`
        # and the entry copies it as `profile_kind`. If that member goes, this
        # surface offers nothing and the map above fails.
        evidence = set(manager.LINE_CHECKPOINT_COLUMNS["evidence"].members)
        return {
            "attempt-assignment": set(attempts.ASSIGNMENT_COLUMNS),
            "checkpoint-verdict": set(manager.CHECKPOINT_VERDICT_COLUMNS),
            "authority-proposal": proposal,
            "accepted-job": {"scope_digest"} if "test_scope" in
            jobs.JOB_COLUMNS else set(),
            "checkpoint-evidence-profile":
                {"profile_kind"} if "profile" in evidence else set(),
        }

    def test_every_member_is_claimed_by_exactly_one_producer(self):
        from baton_v12.integration.queue import ELIGIBILITY_MEMBERS
        self.assertEqual(sorted(self.PRODUCERS), sorted(ELIGIBILITY_MEMBERS))

    def test_every_producer_actually_offers_the_member(self):
        """The check that would have caught all three. Each surface is asked
        whether it carries the name the account says it copies."""
        offered = self.surfaces()
        for member, producer in sorted(self.PRODUCERS.items()):
            with self.subTest(member=member, producer=producer):
                self.assertIn(member, offered[producer],
                              f"{member} claims {producer} and that surface "
                              f"does not offer it")

    def test_the_three_removed_members_have_no_producer_anywhere(self):
        """Why they are gone, driven rather than remembered."""
        from baton_v12.integration.queue import ELIGIBILITY_MEMBERS
        offered = self.surfaces()
        everywhere = set()
        for names in offered.values():
            everywhere |= names
        for gone in ("profile_version", "profile_account_digest",
                     "proposal_manifest_digest"):
            with self.subTest(member=gone):
                self.assertNotIn(gone, everywhere)
                self.assertNotIn(gone, ELIGIBILITY_MEMBERS)

    def test_the_profile_kind_is_one_the_producer_can_emit(self):
        """W101714's first review: the fixture asserted `repository`, and the
        named producer emits `generic` or `git`."""
        from baton_v12.source_profiles import PROFILES
        self.assertIn(eligibility()["profile_kind"], PROFILES)
        self.assertIn(self.place("entry-1")["profile_kind"], PROFILES)

    def test_the_accepted_evidence_carries_the_member_this_one_renames(self):
        """The non-vacuity the second review asked for.

        `profile_kind` is a RENAME of the accepted checkpoint evidence's
        `profile`, and this reads W71918's own contract --
        `LINE_CHECKPOINT_COLUMNS["evidence"].members` -- rather than a set
        literal. If the accepted evidence ever drops `profile`, this fails
        here AND the producer map above fails, which is the whole point: the
        previous version of this proof would have kept passing.
        """
        from baton_v12.worker_manager import schema as manager
        members = manager.LINE_CHECKPOINT_COLUMNS["evidence"].members
        self.assertIn("profile", members)
        self.assertNotIn("profile_kind", members)
        self.assertEqual(self.surfaces()["checkpoint-evidence-profile"],
                         {"profile_kind"})

    def test_the_account_carries_the_exact_value_the_producer_writes(self):
        """`checkpoint_profiles.GitCheckpointProfile.freeze` puts
        `source_profiles.GIT_PROFILE` in the evidence's `profile` member, so
        the account's copy is compared to that constant rather than to a word
        this suite chose. Freezing for real needs a repository and a command
        runner, which is Git reaching into a suite whose subject is a
        coordinator that must not know what Git is."""
        import inspect
        from baton_v12 import checkpoint_profiles
        from baton_v12.source_profiles import GIT_PROFILE
        self.assertEqual(eligibility()["profile_kind"], GIT_PROFILE)
        self.assertEqual(self.place("entry-1")["profile_kind"], GIT_PROFILE)
        # And the producer really writes that constant into that member.
        frozen = inspect.getsource(checkpoint_profiles.GitCheckpointProfile
                                   .freeze)
        self.assertIn('"profile": GIT_PROFILE', frozen)

    def test_the_computed_digests_are_computed_the_producer_s_way(self):
        """`path_set_digest` is `digest(paths)` -- `checkpoint_profiles` and
        `review_cycles` both refuse evidence where it is not -- and
        `scope_digest` is the digest of the accepted Job's own `test_scope`."""
        from baton_v12.contracts import digest
        from .fixtures import PATHS, TEST_SCOPE
        placed = self.place("entry-1")
        self.assertEqual(placed["path_set_digest"], digest(PATHS))
        self.assertEqual(placed["scope_digest"], digest(TEST_SCOPE))
        self.assertEqual(PATHS, sorted(set(PATHS)))

    def test_the_account_the_store_returns_is_the_account_that_was_admitted(self):
        self.assertEqual(self.place("entry-1")["eligibility"], eligibility())


# -- W126887: opening committed coordinator evidence without writing ---------
#
# `work/records/2026/09/finding-v12-composed-ending-consumer/findings/
# finding-readonly-coordinator-open/`.
#
# THE ONLY PUBLIC OPENER CREATES. `IntegrationStore.open` makes an absent
# store, initializes an empty one under `BEGIN IMMEDIATE`, and asks for a
# persistent journal mode -- right for a coordinator about to act, and the
# reason a separate status process had no way to read committed entry, lease
# and history evidence at all.


class ReadOnlyOpening(QueueCase):
    """The new opener: an existing coordinator, read, and left as found."""

    def entries_on_disk(self):
        return sorted(os.listdir(self.root))

    def snapshot_bytes(self):
        """The coordinator's own bytes and mode, sidecars excluded.

        The `-wal` and `-shm` beside a held store belong to the serving
        coordinator and move as it works; what this measures is that a
        read-only open changes no byte of the store itself.
        """
        return {name: (open(os.path.join(self.root, name), "rb").read(),
                       stat.S_IMODE(os.stat(os.path.join(self.root,
                                                         name)).st_mode))
                for name in self.entries_on_disk()
                if not name.endswith(("-wal", "-shm"))}

    def reading(self, path=None):
        held = IntegrationStore.open_readonly(path or self.path,
                                              incarnation="reader-1",
                                              clock=self.clock)
        self.addCleanup(held.close)
        return held

    # -- what it reads --------------------------------------------------------

    def test_it_opens_a_held_store_and_reads_its_committed_entries(self):
        self.place("entry-1")
        held = self.reading()
        # THE PUBLIC READERS, over the read-only handle: exactly the interface
        # the pinned API says it keeps.
        self.assertEqual([one["entry_id"] for one in entries_of(held, TARGET)],
                         ["entry-1"])
        self.assertEqual(target_of(held, TARGET)["canonical_target_id"],
                         TARGET)
        self.assertEqual(held.incarnation, "reader-1")

    def test_the_public_lease_reader_still_answers(self):
        self.place("entry-1")
        self.lease()
        held = self.reading()
        self.assertEqual(lease_of(held, "lease-1")["lease_id"], "lease-1")
        # AND THE POSSESSION PROOF, which reads the target, the entry, the
        # lease and the fence together -- the composed read this store's own
        # snapshot exists for, answered over a handle that cannot write.
        self.assertIsNotNone(live_grant(
            held, lease_id="lease-1", canonical_target_id=TARGET,
            entry_id="entry-1",
            fence=target_of(held, TARGET)["fence"]))

    def test_it_reads_data_committed_after_it_was_opened(self):
        """THE CASE THIS OPENER EXISTS FOR. A coordinator holds the store and
        keeps committing; a separate reading handle sees each committed state,
        not a frozen one and not a stale one."""
        self.place("entry-1")
        held = self.reading()
        self.assertEqual(len(entries_of(held, TARGET)), 1)
        # COMMITTED AFTER THE READER WAS OPENED, by the coordinator that still
        # holds the store.
        self.place("entry-2", checkpoint_id="checkpoint-2")
        self.assertEqual(len(entries_of(held, TARGET)), 2)

    # -- what it will not do --------------------------------------------------

    def test_an_absent_store_is_refused_and_none_is_created(self):
        missing = os.path.join(self.root, "absent.sqlite3")
        with self.assertRaises(ContractRefusal) as caught:
            IntegrationStore.open_readonly(missing, incarnation="reader-1",
                                           clock=self.clock)
        self.assertIn("creates none", caught.exception.message)
        self.assertFalse(os.path.lexists(missing))

    def test_an_empty_database_is_refused_rather_than_initialized(self):
        """`open` would initialize this one. That is the single place this
        opener's answer differs, and the reason it differs."""
        empty = os.path.join(self.root, "empty.sqlite3")
        sqlite3.connect(empty).close()
        before = open(empty, "rb").read()
        with self.assertRaises(ContractRefusal) as caught:
            IntegrationStore.open_readonly(empty, incarnation="reader-1",
                                           clock=self.clock)
        self.assertIn("initializes nothing", caught.exception.message)
        self.assertEqual(open(empty, "rb").read(), before)

    def test_a_foreign_database_is_refused_untouched(self):
        foreign = os.path.join(self.root, "theirs.sqlite3")
        connection = sqlite3.connect(foreign, isolation_level=None)
        connection.execute("CREATE TABLE theirs (a TEXT)")
        connection.close()
        before = open(foreign, "rb").read()
        with self.assertRaises(ContractRefusal) as caught:
            IntegrationStore.open_readonly(foreign, incarnation="reader-1",
                                           clock=self.clock)
        self.assertIn("Nothing was changed", caught.exception.message)
        self.assertEqual(open(foreign, "rb").read(), before)

    def test_a_store_of_another_kind_is_refused_untouched(self):
        foreign = os.path.join(self.root, "other-kind.sqlite3")
        connection = sqlite3.connect(foreign, isolation_level=None)
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, "
                           "value TEXT NOT NULL)")
        connection.execute("INSERT INTO meta VALUES (?, ?)",
                           ("store_kind", "somebody.else/1"))
        connection.close()
        before = open(foreign, "rb").read()
        with self.assertRaises(ContractRefusal):
            IntegrationStore.open_readonly(foreign, incarnation="reader-1",
                                           clock=self.clock)
        self.assertEqual(open(foreign, "rb").read(), before)

    def test_its_operands_are_owned_exactly_as_the_serving_opener_owns_them(
            self):
        for operands in ({"incarnation": "", "clock": self.clock},
                         {"incarnation": "reader-1", "clock": None}):
            with self.subTest(**{k: type(v).__name__
                                 for k, v in operands.items()}):
                with self.assertRaises(ContractRefusal):
                    IntegrationStore.open_readonly(self.path, **operands)

    # -- and it performs nothing ---------------------------------------------

    def test_a_transition_refuses_before_the_transaction(self):
        held = self.reading()
        reached = []
        with self.assertRaises(ContractRefusal) as caught:
            held.transact("operation-1", "integration.enqueue", "signature",
                          lambda connection: reached.append(True),
                          witness=lambda *arguments: None)
        self.assertEqual(caught.exception.category, "refused")
        self.assertEqual(caught.exception.code, "capability")
        self.assertIn("journals nothing", caught.exception.message)
        self.assertEqual(reached, [])

    def test_reading_changes_no_store_byte(self):
        self.place("entry-1")
        before, listed = self.snapshot_bytes(), self.entries_on_disk()
        held = IntegrationStore.open_readonly(self.path,
                                              incarnation="reader-1",
                                              clock=self.clock)
        try:
            entries_of(held, TARGET)
        finally:
            held.close()
        self.assertEqual(self.entries_on_disk(), listed)
        self.assertEqual(self.snapshot_bytes(), before)

    def test_the_serving_coordinator_is_undisturbed(self):
        self.place("entry-1")
        held = self.reading()
        entries_of(held, TARGET)
        # IT STILL COMMITS AFTERWARDS, which is what "leaves the store alone"
        # has to mean for a coordinator two Authorities may be contending for.
        self.place("entry-after", checkpoint_id="checkpoint-2")

    def owned_store(self, name, **meta):
        """A database carrying this coordinator's own metadata, plus overrides.

        Used for the version case, which needs a store this build OWNS and
        cannot speak -- `_adopt` refuses on kind before it looks at version,
        so a foreign kind would answer the wrong question.
        """
        from baton_v12.integration.schema import STORE_KIND

        path = os.path.join(self.root, name)
        connection = sqlite3.connect(path, isolation_level=None)
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, "
                           "value TEXT NOT NULL)")
        held = {"store_kind": STORE_KIND, "schema_version": "1"}
        held.update(meta)
        for key, value in held.items():
            connection.execute("INSERT INTO meta VALUES (?, ?)", (key, value))
        connection.close()
        return path

    def test_a_partial_sidecar_pair_reads_the_same_committed_evidence(self):
        """CONVERTED under owner M128251, over the two states the earlier
        review drove: only `-wal` beside the store, and only `-shm`.

        This used to require a refusal, because completing the pair is
        SQLite's own act on a `mode=ro` connection. The amendment permits
        exactly that, so what is asserted now is that each state opens SAFELY
        and answers the same committed entry -- and that the coordinator's own
        bytes are the same afterwards as before.
        """
        for one in ("-wal", "-shm"):
            with self.subTest(present=one):
                self.setUp()
                self.place("entry-1")
                self.coordinator.close()
                for other in ("-wal", "-shm"):
                    if os.path.lexists(self.path + other):
                        os.unlink(self.path + other)
                open(self.path + one, "wb").close()
                before = self.snapshot_bytes()
                held = IntegrationStore.open_readonly(
                    self.path, incarnation="reader-1", clock=self.clock)
                try:
                    self.assertEqual(
                        [one["entry_id"] for one in entries_of(held, TARGET)],
                        ["entry-1"])
                finally:
                    held.close()
                self.assertEqual(self.snapshot_bytes(), before)

    def test_a_file_sqlite_cannot_read_refuses_in_this_taxonomy(self):
        """REVIEW [P2]. `sqlite3.DatabaseError` came straight out of a public
        opener, so a caller handling this coordinator's refusals received an
        uncontrolled error for an unavailable read."""
        prose = os.path.join(self.root, "prose.txt")
        with open(prose, "wb") as handle:
            handle.write(b"this is not a database\n")
        before = open(prose, "rb").read()
        with self.assertRaises(ContractRefusal) as caught:
            IntegrationStore.open_readonly(prose, incarnation="reader-1",
                                           clock=self.clock)
        self.assertEqual(caught.exception.category, "refused")
        self.assertIn("could not be read by this coordinator",
                      caught.exception.message)
        self.assertEqual(open(prose, "rb").read(), before)

    def test_an_unrelated_failure_is_not_swallowed(self):
        """Only SQLite's own failures are translated."""
        self.place("entry-1")
        with mock.patch.object(IntegrationStore, "_objects",
                               side_effect=MemoryError("not sqlite's")):
            with self.assertRaises(MemoryError):
                IntegrationStore.open_readonly(self.path,
                                               incarnation="reader-1",
                                               clock=self.clock)

    def test_a_store_at_another_schema_version_is_refused_untouched(self):
        path = self.owned_store("older.sqlite3", schema_version="0")
        before = open(path, "rb").read()
        with self.assertRaises(ContractRefusal):
            IntegrationStore.open_readonly(path, incarnation="reader-1",
                                           clock=self.clock)
        self.assertEqual(open(path, "rb").read(), before)

    def test_a_read_only_filesystem_store_is_readable(self):
        """Where the platform supports it: the directory is not writable and a
        held coordinator still reads."""
        self.place("entry-1")
        before = stat.S_IMODE(os.stat(self.root).st_mode)
        try:
            os.chmod(self.root, 0o500)
        except OSError:
            self.skipTest("this platform will not make the root read-only")
        self.addCleanup(os.chmod, self.root, before)
        if os.access(self.root, os.W_OK):
            self.skipTest("this process writes regardless of the mode")
        held = self.reading()
        self.assertEqual([one["entry_id"] for one in entries_of(held, TARGET)],
                         ["entry-1"])

    def test_the_committed_history_backs_every_read_it_answers(self):
        """THE JOURNAL IS WHAT THESE READERS PROVE AGAINST.

        `entries_of` does not report rows; it agrees them with this
        coordinator's own committed history and refuses a set the journal does
        not account for. So a reader that answers here has read that history
        -- and one whose journal has been emptied refuses, which is what makes
        the positive above a statement about committed evidence rather than
        about a table.
        """
        self.place("entry-1")
        held = self.reading()
        self.assertTrue(entries_of(held, TARGET))
        # THE SAME READ, WITH THE HISTORY TAKEN AWAY. The forgery is made
        # through the serving handle, which is the only one that can write.
        self.coordinator._connection.execute("DELETE FROM operations")
        with self.assertRaises(ContractRefusal):
            entries_of(held, TARGET)

    def test_a_store_nobody_holds_reads_its_committed_evidence(self):
        """CONVERTED under owner M128251. This is the case the whole Work is
        for.

        SQLite creates `-wal` and `-shm` when it opens a write-ahead-log
        database that has neither -- from a `mode=ro` connection too, because
        they are coordination files rather than the database. This used to be
        refused. The amendment settles that they are SQLite's to make, so a
        status process can now read a coordinator AFTER AN ORDINARY SERVING
        SHUTDOWN, which is when there is no serving process left to ask.
        """
        self.place("entry-1")
        # THE FIXTURE'S OWN COORDINATOR IS CLOSED FIRST, so nobody holds the
        # store: that is the state this read is about. `before` is measured
        # AFTER the close, because a clean shutdown checkpoints the
        # write-ahead log into the database -- the writer's act, not this
        # reader's, and measuring across it would charge it to the opener.
        self.coordinator.close()
        before = self.snapshot_bytes()
        held = IntegrationStore.open_readonly(self.path,
                                              incarnation="reader-1",
                                              clock=self.clock)
        try:
            self.assertEqual(
                [one["entry_id"] for one in entries_of(held, TARGET)],
                ["entry-1"])
        finally:
            held.close()
        # THE DATABASE IS UNCHANGED, which is the protection that did not
        # move; the sidecars beside it are SQLite's and the amendment says so.
        self.assertEqual(self.snapshot_bytes(), before)

    def test_no_coordinator_is_created_where_none_exists(self):
        """THE PROTECTION THE AMENDMENT DID NOT TOUCH, kept explicit beside
        the conversions above: sidecars are SQLite's, and a coordinator is
        not."""
        missing = os.path.join(self.root, "absent.sqlite3")
        before = self.entries_on_disk()
        with self.assertRaises(ContractRefusal) as caught:
            IntegrationStore.open_readonly(missing, incarnation="reader-1",
                                           clock=self.clock)
        self.assertEqual(caught.exception.category, "refused")
        self.assertIn("creates none", caught.exception.message)
        self.assertEqual(self.entries_on_disk(), before)
