"""W71877 -- durable pooled implementation and review scheduling."""

import json
import threading
import sqlite3
from types import SimpleNamespace

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (POOL_SCHEMA, JobStore, PooledManagerOperations,
                                   activate_pool, allocation_of,
                                   allocation_rows, check_binding, job_of,
                                   pool_workers, reserve, status, submit, sweep)
from baton_v12.job_manager import episodes, scheduler
from baton_v12.worker_manager import AuthorityPort, accept_offer

from .fixtures import (NOW, PROFILE, UUID, FakeSession, JobManagerCase,
                       _unobserved, fake_claim_signature, job, stage,
                       submission)


def worker(worker_id, lane, participant, kinds):
    return {"worker_id": worker_id, "lane": lane,
            "participant": participant, "profile_name": "reference",
            "profile_digest": PROFILE, "eligible_kinds": kinds}


def pool(variant="primary", workers=None):
    return {"schema": POOL_SCHEMA, "variant": variant,
            "separation_class": "provider-diverse",
            "workers": workers if workers is not None else [
                worker("impl-a", "implementation", "baton.impl-a",
                       ["implementation", "integration"]),
                worker("impl-b", "implementation", "baton.impl-b",
                       ["implementation"]),
                worker("review-a", "review", "baton.review-a", ["review"]),
                worker("review-b", "review", "baton.review-b", ["review"])]}


def principals(document, aliases=None):
    aliases = aliases or {}
    return {entry["participant"]: aliases.get(
        entry["participant"], "principal:" + entry["worker_id"])
        for entry in document["workers"]}


class PoolCase(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.jobs = self.store()

    def activate(self, document=None, resolved=None):
        document = document or pool()
        return activate_pool(self.jobs, document,
                             resolved if resolved is not None
                             else principals(document))

    def attempts(self, jobs):
        submit(self.jobs, submission(jobs=jobs))
        return [self.attempting(self.jobs, one["job_id"] + "/" +
                                one["stages"][0]["kind"])
                for one in jobs]


class PoolDocuments(PoolCase):

    def test_activation_persists_the_complete_normalized_generation(self):
        answer = self.activate()
        self.assertEqual(answer["generation"], 1)
        self.assertEqual(answer["variant"], "primary")
        self.assertEqual(len(pool_workers(self.jobs)), 4)
        self.assertEqual({row["canonical_principal"]
                          for row in pool_workers(self.jobs)},
                         {"principal:impl-a", "principal:impl-b",
                          "principal:review-a", "principal:review-b"})

    def test_reattachment_revalidates_principals_and_does_not_rewrite(self):
        document = pool()
        first = self.activate(document)
        self.assertEqual(self.activate(document), first)
        changed = principals(document)
        changed["baton.impl-a"] = "principal:changed"
        with self.assertRaises(ContractRefusal):
            self.activate(document, changed)
        self.assertEqual(len(pool_workers(self.jobs)), 4)

    def test_a_new_variant_is_a_new_generation(self):
        self.activate()
        second = pool("fallback")
        self.assertEqual(self.activate(second)["generation"], 2)
        self.assertEqual(len(pool_workers(self.jobs, 1)), 4)
        self.assertEqual(len(pool_workers(self.jobs, 2)), 4)

    def test_cross_lane_eligibility_is_refused(self):
        document = pool(workers=[worker("wrong", "review", "baton.wrong",
                                                 ["implementation"])])
        with self.assertRaises(ContractRefusal):
            self.activate(document)

    def test_schema_three_migrates_atomically_to_empty_scheduler_relations(self):
        self.jobs.close()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        for table in ("worker_affinity", "stage_allocations", "pool_workers",
                      "pool_generations"):
            connection.execute(f"DROP TABLE {table}")
        connection.execute("UPDATE meta SET value = '3' WHERE key = ?",
                           ("schema_version",))
        connection.close()
        migrated = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-migrated", clock=self.clock)
        self.addCleanup(migrated.close)
        self.assertEqual(pool_workers(migrated), [])
        objects = {row[0] for row in migrated._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertTrue({"pool_generations", "pool_workers",
                         "stage_allocations", "worker_affinity"} <= objects)


class Capacity(PoolCase):

    def test_two_implementation_and_two_review_capacities_are_live_together(self):
        self.activate()
        jobs = [job("impl-1", stages=[stage("implementation", "work:i1")]),
                job("impl-2", stages=[stage("implementation", "work:i2")]),
                job("review-1", stages=[stage("review", "work:r1")]),
                job("review-2", stages=[stage("review", "work:r2")])]
        allocated = [reserve(self.jobs, attempt)
                     for attempt in self.attempts(jobs)]
        self.assertEqual([one["allocation_state"] for one in allocated],
                         ["reserved"] * 4)
        self.assertEqual(len({one["canonical_principal"]
                              for one in allocated}), 4)

    def test_participant_aliases_contribute_one_effective_capacity(self):
        document = pool(workers=[
            worker("impl-a", "implementation", "baton.alias-a",
                   ["implementation"]),
            worker("impl-b", "implementation", "baton.alias-b",
                   ["implementation"])])
        self.activate(document, principals(document, {
            "baton.alias-a": "principal:one",
            "baton.alias-b": "principal:one"}))
        first, second = self.attempts([
            job("one", stages=[stage("implementation", "work:one")]),
            job("two", stages=[stage("implementation", "work:two")])])
        reserve(self.jobs, first)
        with self.assertRaises(ContractRefusal) as caught:
            reserve(self.jobs, second)
        self.assertEqual(caught.exception.code, "precondition")
        self.assertEqual(len(allocation_rows(self.jobs)), 1)

    def test_capacity_miss_does_not_hide_an_unrelated_review_slot(self):
        self.activate()
        attempts = self.attempts([
            job("impl-1", stages=[stage("implementation", "work:i1")]),
            job("impl-2", stages=[stage("implementation", "work:i2")]),
            job("impl-3", stages=[stage("implementation", "work:i3")]),
            job("review-1", stages=[stage("review", "work:r1")])])
        reserve(self.jobs, attempts[0])
        reserve(self.jobs, attempts[1])
        with self.assertRaises(ContractRefusal):
            reserve(self.jobs, attempts[2])
        self.assertEqual(reserve(self.jobs, attempts[3])["lane"], "review")

    def test_one_stage_episode_wins_a_two_connection_reservation_race(self):
        self.activate()
        attempt = self.attempts([
            job("race", stages=[stage("implementation", "work:race")])])[0]
        barrier = threading.Barrier(2)
        answers = []

        def compete(incarnation):
            store = JobStore.open(self.job_path, authority_uuid=UUID,
                                  incarnation=incarnation, clock=self.clock)
            try:
                local = self.attempting(store, "race/implementation")
                barrier.wait()
                answers.append(reserve(store, local)["assignment_id"])
            finally:
                store.close()

        threads = [threading.Thread(target=compete, args=(f"jobs-{n}",))
                   for n in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(answers, [attempt["attempt_id"]] * 2)
        self.assertEqual(len(allocation_rows(self.jobs)), 1)


class SelectionAndSettlement(PoolCase):

    def test_affinity_is_soft_and_fallback_does_not_rewrite_it(self):
        self.activate()
        first, blocker, fallback = self.attempts([
            job("first", stages=[stage("implementation", "work:line")]),
            job("blocker", stages=[stage("implementation", "work:block")]),
            job("fallback", stages=[stage("implementation", "work:line")])])
        original = reserve(self.jobs, first)
        scheduler.release(self.jobs, first["attempt_id"], "completed")
        occupied = reserve(self.jobs, blocker)
        self.assertEqual(occupied["worker_id"], original["worker_id"])
        selected = reserve(self.jobs, fallback)
        self.assertEqual(selected["selection_outcome"], "fallback")
        self.assertEqual(selected["preferred_worker_id"], original["worker_id"])
        affinity = self.jobs._connection.execute(
            "SELECT worker_id FROM worker_affinity WHERE development_line = ?",
            ("work:line",)).fetchone()[0]
        self.assertEqual(affinity, original["worker_id"])

    def test_an_abandoned_offer_releases_only_its_allocation(self):
        self.activate()
        first, second = self.attempts([
            job("one", stages=[stage("implementation", "work:one")]),
            job("two", stages=[stage("implementation", "work:two")])])
        reserve(self.jobs, first)
        reserve(self.jobs, second)
        ended = episodes.end_episode(
            self.jobs, episodes.live_of(self.jobs, first["stage_id"]),
            "abandoned-after-restart", 1)
        self.assertEqual(ended["ended_state"], "abandoned-after-restart")
        scheduler.reconcile_allocations(self.jobs)
        self.assertEqual(allocation_of(
            self.jobs, first["attempt_id"])["allocation_state"], "released")
        self.assertEqual(allocation_of(
            self.jobs, second["attempt_id"])["allocation_state"], "reserved")

    def test_every_no_assignment_ending_releases_capacity(self):
        self.activate()
        for ordinal, ending in enumerate(sorted(scheduler.RELEASE_ENDINGS)):
            with self.subTest(ending=ending):
                job_id = f"ending-{ordinal}"
                submit(self.jobs, submission(f"sub-ending-{ordinal}", jobs=[
                    job(job_id, stages=[stage(
                        "implementation", f"work:{job_id}")])]))
                attempt = self.attempting(
                    self.jobs, f"{job_id}/implementation")
                reserve(self.jobs, attempt)
                episodes.end_episode(
                    self.jobs, episodes.live_of(
                        self.jobs, attempt["stage_id"]), ending, ordinal + 1)
                scheduler.reconcile_allocations(self.jobs)
                self.assertEqual(allocation_of(
                    self.jobs, attempt["attempt_id"])["allocation_state"],
                    "released")

    def test_uncertain_runtime_quarantines_one_allocation(self):
        self.activate()
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        reserve(self.jobs, attempt)
        held = {attempt["stage_id"]: {
            "attempt": attempt,
            "observed": {"runtime": {"execution_runtime": "uncertain",
                                       "cleanup": None},
                         "start_failure": None,
                         "preparation_failure": None}}}
        scheduler.reconcile_allocations(self.jobs, held)
        self.assertEqual(allocation_of(
            self.jobs, attempt["attempt_id"])["allocation_state"],
                         "recovery-required")

    def test_completed_cleanup_releases_capacity(self):
        self.activate()
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        reserve(self.jobs, attempt)
        held = {attempt["stage_id"]: {
            "attempt": attempt,
            "observed": {"runtime": {"execution_runtime": "destroyed",
                                       "cleanup": "retained"},
                         "start_failure": None,
                         "preparation_failure": None}}}
        scheduler.reconcile_allocations(self.jobs, held)
        self.assertEqual(allocation_of(
            self.jobs, attempt["attempt_id"])["allocation_state"], "released")

    def test_no_static_eligible_worker_is_exceptional_not_forever_deferred(self):
        document = pool(workers=[
            worker("review-a", "review", "baton.review-a", ["review"])])
        self.activate(document)
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        with self.assertRaises(ContractRefusal) as caught:
            reserve(self.jobs, attempt)
        self.assertTrue(caught.exception.durable)
        from baton_v12.job_manager import Unobserved
        projected = status(self.jobs, Unobserved(), observed_at=NOW)
        self.assertEqual(projected["jobs"][0]["stages"][0]["state"],
                         "exceptional")

    def test_review_excludes_the_producers_canonical_principal(self):
        document = pool(workers=[
            worker("impl", "implementation", "baton.impl",
                   ["implementation"]),
            worker("review", "review", "baton.review", ["review"])])
        self.activate(document, {"baton.impl": "principal:shared",
                                 "baton.review": "principal:shared"})
        submit(self.jobs, submission(jobs=[
            job("line", stages=[stage("implementation", "work:impl"),
                                stage("review", "work:review")])]))
        implementation = self.attempting(self.jobs, "line/implementation")
        review = self.attempting(self.jobs, "line/review")
        reserve(self.jobs, implementation)
        scheduler.release(self.jobs, implementation["attempt_id"], "completed")
        with self.assertRaises(ContractRefusal) as caught:
            reserve(self.jobs, review)
        self.assertTrue(caught.exception.durable)

    def test_external_opinion_exclusions_compare_all_three_identities(self):
        document = pool(workers=[
            worker("review-a", "review", "baton.review-a", ["review"]),
            worker("review-b", "review", "baton.review-b", ["review"]),
            worker("review-c", "review", "baton.review-c", ["review"]),
            worker("review-d", "review", "baton.review-d", ["review"])])
        resolved = principals(document)
        self.activate(document, resolved)
        attempt = self.attempts([
            job("opinion", stages=[stage("review", "work:opinion")])])[0]
        selected = reserve(self.jobs, attempt, excluded={
            "worker_ids": {"review-a"},
            "participants": {"baton.review-b"},
            "principals": {resolved["baton.review-c"]}})
        self.assertEqual(selected["worker_id"], "review-d")

    def test_status_exposes_all_three_scheduler_identities(self):
        self.activate()
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        allocation = reserve(self.jobs, attempt)
        from baton_v12.job_manager import Unobserved
        found = status(self.jobs, Unobserved(), observed_at=NOW)
        stage_status = found["jobs"][0]["stages"][0]
        self.assertEqual(stage_status["attempt_id"], allocation["assignment_id"])
        self.assertEqual(stage_status["allocation"]["worker_id"],
                         allocation["worker_id"])
        self.assertEqual(stage_status["allocation"]["canonical_principal"],
                         allocation["canonical_principal"])
        self.assertEqual(stage_status["allocation"]["variant"], "primary")
        self.assertEqual(stage_status["allocation"]["separation_class"],
                         "provider-diverse")


class _ClaimingStub:

    def __init__(self, participant, principal):
        self.port = SimpleNamespace(participant=participant)
        self.principal = principal

    def claim(self, stage):
        return {"decision": {"principal": self.principal}}

    def canonical_operation(self, act, offer_id):
        return f"offer.{'issue' if act == 'admit' else 'settle'}:{offer_id}"

    def receipt_of(self, operation_id):
        return None

    def observe(self, stage):
        return _unobserved()


class ClaimBinding(PoolCase):

    def test_claim_principal_mismatch_quarantines_the_allocation(self):
        document = pool(workers=[
            worker("impl", "implementation", "baton.impl",
                   ["implementation"])])
        self.activate(document, {"baton.impl": "principal:wanted"})
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        reserve(self.jobs, attempt)
        pooled = PooledManagerOperations(
            self.jobs, {(1, "impl"): _ClaimingStub(
                "baton.impl", "principal:wrong")},
            resolved_principals={"baton.impl": "principal:wanted"})
        with self.assertRaises(ContractRefusal) as caught:
            pooled.claim(attempt)
        self.assertEqual(caught.exception.code, "identity-mismatch")
        self.assertEqual(allocation_of(
            self.jobs, attempt["attempt_id"])["allocation_state"],
                         "recovery-required")

    def test_claim_adopts_the_exact_reserved_principal(self):
        document = pool(workers=[
            worker("impl", "implementation", "baton.impl",
                   ["implementation"])])
        self.activate(document, {"baton.impl": "principal:wanted"})
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        reserve(self.jobs, attempt)
        pooled = PooledManagerOperations(
            self.jobs, {(1, "impl"): _ClaimingStub(
                "baton.impl", "principal:wanted")},
            resolved_principals={"baton.impl": "principal:wanted"})
        answer = pooled.claim(attempt)
        self.assertEqual(answer["decision"]["principal"], "principal:wanted")
        self.assertEqual(allocation_of(
            self.jobs, attempt["attempt_id"])["allocation_state"], "reserved")


class TheMigrationProvesTheSchemaItMigratesFrom(PoolCase):
    """W71877 review [P1]: the 3 -> 4 step validated meta, the Authority
    binding and the FINISHED table names, and nothing about the schema it was
    migrating from.

    The reviewer stamped a store as schema 3 with `episodes_one_live_per_stage`
    removed; it opened as schema 4 with the critical one-live-episode index
    still missing. A version stamp is a claim and the objects are the evidence.
    """

    def stamped_as_three(self, spoil=()):
        """This case's store, reduced to schema 3 and then spoiled.

        Reduced the way a real schema-3 store differs from this one: the four
        relations the 3 -> 4 step creates are dropped and the version is put
        back. `spoil` is whatever the case is actually about.
        """
        self.jobs.close()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        try:
            for table in ("worker_affinity", "stage_allocations",
                          "pool_workers", "pool_generations"):
                connection.execute(f"DROP TABLE {table}")
            for statement in spoil:
                connection.execute(statement)
            connection.execute("UPDATE meta SET value = '3' WHERE key = ?",
                               ("schema_version",))
        finally:
            connection.close()

    def reopen(self, incarnation="jobs-migrated"):
        store = JobStore.open(self.job_path, authority_uuid=UUID,
                              incarnation=incarnation, clock=self.clock)
        self.addCleanup(store.close)
        return store

    def unchanged(self):
        """What the store still says about itself after a refused migration."""
        connection = sqlite3.connect(self.job_path)
        try:
            version = connection.execute(
                "SELECT value FROM meta WHERE key = 'schema_version'"
            ).fetchone()[0]
            objects = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        finally:
            connection.close()
        return version, objects

    def test_a_whole_schema_three_store_migrates(self):
        """The positive case, so the refusals below are about the spoiling."""
        self.stamped_as_three()
        migrated = self.reopen()
        self.assertEqual(pool_workers(migrated), [])
        version, objects = self.unchanged()
        self.assertEqual(version, "4")
        self.assertIn("stage_allocations", objects)

    def test_a_missing_index_refuses_and_changes_nothing(self):
        """The reviewer's exact reproduction."""
        self.stamped_as_three(["DROP INDEX episodes_one_live_per_stage"])
        with self.assertRaises(ContractRefusal) as caught:
            self.reopen()
        self.assertIn("episodes_one_live_per_stage",
                      caught.exception.message)
        self.assertIn("Nothing was changed", caught.exception.message)
        version, objects = self.unchanged()
        self.assertEqual(version, "3")
        self.assertNotIn("pool_generations", objects)
        self.assertNotIn("episodes_one_live_per_stage", objects)

    def test_a_changed_column_refuses_and_changes_nothing(self):
        self.stamped_as_three([
            "ALTER TABLE stages ADD COLUMN improvised TEXT"])
        with self.assertRaises(ContractRefusal) as caught:
            self.reopen()
        self.assertIn("changed stages", caught.exception.message)
        version, objects = self.unchanged()
        self.assertEqual(version, "3")
        self.assertNotIn("pool_generations", objects)

    def test_a_reversed_index_predicate_refuses_and_changes_nothing(self):
        """W71877's second correction review: the SAFETY RULE is the predicate.

        `episodes_one_live_per_stage` is unique on `stage_id` WHERE the episode
        has not ended. An index with the same name, the same uniqueness and the
        same column list but `IS NOT NULL` permits any number of LIVE episodes
        for one stage -- which is the whole thing the index exists to prevent.

        My first version of this validator compared columns, foreign keys and
        index column lists through pragmas, and none of those can see a partial
        predicate. The reviewer's probe migrated cleanly. The definition is
        what is compared now.
        """
        self.stamped_as_three([
            "DROP INDEX episodes_one_live_per_stage",
            "CREATE UNIQUE INDEX episodes_one_live_per_stage "
            "ON episodes (stage_id) WHERE ended_state IS NOT NULL"])
        with self.assertRaises(ContractRefusal) as caught:
            self.reopen()
        self.assertIn("changed episodes_one_live_per_stage",
                      caught.exception.message)
        version, objects = self.unchanged()
        self.assertEqual(version, "3")
        self.assertNotIn("pool_generations", objects)

    def test_a_changed_check_constraint_refuses_and_changes_nothing(self):
        """The other rule a pragma cannot see.

        `episodes`' ending CHECK is all-three-or-none: a row naming a state
        without the revision that asserted it is an ending nothing can order
        against the next assertion. A table rebuilt with that CHECK weakened
        keeps every column, every foreign key and every index -- and loses the
        invariant.
        """
        self.stamped_as_three([
            "ALTER TABLE episodes RENAME TO episodes_old",
            "CREATE TABLE episodes ("
            " stage_id TEXT NOT NULL REFERENCES stages(stage_id),"
            " episode INTEGER NOT NULL CHECK (episode >= 1),"
            " offer_id TEXT NOT NULL UNIQUE,"
            " attempt_id TEXT NOT NULL UNIQUE,"
            " opened_at TEXT NOT NULL,"
            " incarnation TEXT NOT NULL,"
            " ended_state TEXT, ended_revision INTEGER, ended_at TEXT,"
            " PRIMARY KEY (stage_id, episode))",
            "INSERT INTO episodes SELECT stage_id, episode, offer_id, "
            "attempt_id, opened_at, incarnation, ended_state, "
            "ended_revision, ended_at FROM episodes_old",
            "DROP TABLE episodes_old",
            "CREATE UNIQUE INDEX episodes_one_live_per_stage "
            "ON episodes (stage_id) WHERE ended_state IS NULL"])
        with self.assertRaises(ContractRefusal) as caught:
            self.reopen()
        self.assertIn("changed episodes", caught.exception.message)
        version, objects = self.unchanged()
        self.assertEqual(version, "3")
        self.assertNotIn("pool_generations", objects)

    def test_the_two_legitimate_spellings_of_one_schema_both_migrate(self):
        """The comparison is about CONTENT, and this is what protects that.

        A store that arrived at schema 3 by MIGRATING carries `MIGRATIONS[1]`'s
        DDL -- SQLite rewrites a renamed table's header as `CREATE TABLE
        "stages"`, quoted, and that step's copy of `episodes` has none of
        `SCHEMA`'s explanatory comments. A store INSTALLED at 3 carries the
        install's text. Both are the same schema, and a comparison that called
        them different would refuse a perfectly good store for its typography.
        """
        from baton_v12.job_manager.store import _definition

        self.stamped_as_three([
            "ALTER TABLE stages RENAME TO stages_2",
            "ALTER TABLE stages_2 RENAME TO stages"])
        connection = sqlite3.connect(self.job_path)
        try:
            spelled = connection.execute(
                "SELECT sql FROM sqlite_master WHERE name = 'stages'"
            ).fetchone()[0]
        finally:
            connection.close()
        # The rename really did change the recorded text ...
        self.assertIn('"stages"', spelled)
        # ... and the definition it means is the same one.
        self.assertNotIn('"', _definition(spelled))
        self.reopen()
        self.assertEqual(self.unchanged()[0], "4")

    def test_an_extra_object_refuses_and_changes_nothing(self):
        self.stamped_as_three([
            "CREATE TABLE somebody_elses (one TEXT PRIMARY KEY)"])
        with self.assertRaises(ContractRefusal) as caught:
            self.reopen()
        self.assertIn("unexpected somebody_elses", caught.exception.message)
        self.assertEqual(self.unchanged()[0], "3")

    def test_a_missing_table_refuses_and_changes_nothing(self):
        self.stamped_as_three(["DROP TABLE receipts"])
        with self.assertRaises(ContractRefusal) as caught:
            self.reopen()
        self.assertIn("missing receipts", caught.exception.message)
        self.assertEqual(self.unchanged()[0], "3")

    def test_two_concurrent_migrations_leave_one_store(self):
        """Both openers see schema 3; the lock decides and the loser adopts.

        The validation runs inside that same transaction, so a waiter that
        arrives after the winner committed must not re-run it against a store
        that is already schema 4 -- it would find the scheduler relations it
        does not expect and refuse a perfectly good store.
        """
        self.stamped_as_three()
        answers = []
        barrier = threading.Barrier(2, timeout=5)

        def opening(incarnation):
            def run():
                try:
                    barrier.wait()
                except threading.BrokenBarrierError:
                    pass
                try:
                    store = JobStore.open(self.job_path, authority_uuid=UUID,
                                          incarnation=incarnation,
                                          clock=self.clock)
                    answers.append(pool_workers(store))
                    store.close()
                except BaseException as failure:
                    answers.append(failure)
            return run

        threads = [threading.Thread(target=opening(one))
                   for one in ("jobs-a", "jobs-b")]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
        for thread in threads:
            self.assertFalse(thread.is_alive())
        self.assertEqual(answers, [[], []], answers)
        self.assertEqual(self.unchanged()[0], "4")


class TheReviewedSchedulerGaps(PoolCase):
    """One regression per corrected W71877 review finding.

    Each drives the exact shape the reviewer's retained reproduction drove, so
    a later change that restores the behaviour fails here rather than in the
    next review.
    """

    def one_worker_pool(self, variant="primary", worker_id="impl",
                        participant="baton.impl"):
        return pool(variant, workers=[worker(
            worker_id, "implementation", participant, ["implementation"])])

    # -- [P1] restart revalidates live prior generations ---------------------

    def test_attachment_refuses_a_live_old_generation_that_now_resolves_elsewhere(
            self):
        """The gap: only the generation whose document was handed to
        `activate_pool` was revalidated.

        A live allocation from an older generation keeps that generation's
        worker attached, and nothing asked whether its participant still means
        the same principal. Here the old generation stays live while the
        deployment resolves its participant to somebody else, and attachment
        must refuse before any stage operation -- the later claim-answer
        comparison cannot protect a claim that was taken before the restart.
        """
        old = self.one_worker_pool("primary", "old", "baton.old")
        self.activate(old, {"baton.old": "principal:old"})
        attempt = self.attempts([
            job("old", stages=[stage("implementation", "work:old")])])[0]
        reserve(self.jobs, attempt)
        new = self.one_worker_pool("replacement", "new", "baton.new")
        self.activate(new, {"baton.new": "principal:new"})
        operations = {(1, "old"): _ClaimingStub("baton.old", "principal:old"),
                      (2, "new"): _ClaimingStub("baton.new", "principal:new")}
        # THE ACTIVE GENERATION IS UNCHANGED and only the live prior one moved.
        with self.assertRaises(ContractRefusal) as caught:
            PooledManagerOperations(
                self.jobs, operations,
                resolved_principals={"baton.old": "principal:moved",
                                     "baton.new": "principal:new"})
        self.assertIn("attachment refuses", caught.exception.message)
        # AND THE HONEST RESOLUTION STILL ATTACHES, so the refusal above is
        # about the mismatch rather than about prior generations at all.
        PooledManagerOperations(
            self.jobs, operations,
            resolved_principals={"baton.old": "principal:old",
                                 "baton.new": "principal:new"})

    # -- [P1] no allocation is a refusal, not the first worker ---------------

    def test_a_stage_with_no_allocation_reaches_no_worker(self):
        """The gap: `_worker` fell back to whichever worker sorted first.

        The 3 -> 4 migration creates EMPTY scheduler relations, so an already
        admitted schema-3 stage arrives with an offer and no allocation. Every
        acting operation must refuse it by name.
        """
        document = pool(workers=[
            worker("impl-a", "implementation", "baton.impl-a",
                   ["implementation"]),
            worker("impl-b", "implementation", "baton.impl-b",
                   ["implementation"])])
        resolved = principals(document)
        self.activate(document, resolved)
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        pooled = PooledManagerOperations(
            self.jobs,
            {(1, "impl-a"): _ClaimingStub("baton.impl-a", "principal:impl-a"),
             (1, "impl-b"): _ClaimingStub("baton.impl-b", "principal:impl-b")},
            resolved_principals=resolved)
        for act in ("launch", "dispatch", "conclude"):
            with self.subTest(act=act):
                with self.assertRaises(ContractRefusal) as caught:
                    getattr(pooled, act)(attempt, job_of(self.jobs, "one"))
                self.assertIn("no scheduler allocation",
                              caught.exception.message)
        self.assertIsNone(allocation_of(self.jobs, attempt["attempt_id"]))

    def test_an_unadmitted_stage_is_still_observable(self):
        """The other half, and the reason `_worker` and `_reader` differ.

        One tick observes every live stage, including one that has not been
        admitted yet -- which is how the manager learns it owes an `admit`. A
        stage with no offer has no runtime for any worker to hold, so that read
        must not refuse.
        """
        document = self.one_worker_pool()
        self.activate(document, principals(document))
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        pooled = PooledManagerOperations(
            self.jobs, {(1, "impl"): _ClaimingStub("baton.impl",
                                                   "principal:impl")},
            resolved_principals=principals(document))
        self.assertIsNotNone(pooled.observe(attempt))

    # -- [P1] a durable admission refusal does not release blindly ----------

    def test_a_durable_refusal_after_the_offer_exists_retains_capacity(self):
        """The gap: ANY durable refusal released the allocation.

        `ManagerOperations.admit` commits `issue_offer` before it invokes the
        injected bearer delivery, so a durable delivery refusal arrives with
        the canonical offer already there. Releasing then lets unrelated work
        reserve the same logical worker and principal while that offer may
        still be accepted, which is exactly what the settlement table forbids
        without evidence that no assignment exists.
        """
        from baton_v12.job_manager import ManagerOperations

        document = self.one_worker_pool()
        resolved = principals(document)
        self.activate(document, resolved)
        submit(self.jobs, submission(jobs=[
            job("one", stages=[stage("implementation", "work:one")])]))
        attempt = self.attempting(self.jobs, "one/implementation")
        session = FakeSession("baton.impl", principal="principal:impl")
        session.open_work("work:one")

        def refusing(issued):
            raise ContractRefusal("refused", "precondition",
                                  "the bearer could not be delivered",
                                  durable=True)

        control = self.control()
        operations = ManagerOperations(
            control, AuthorityPort(session, fake_claim_signature),
            mint_bearer=self.mint, deliver_bearer=refusing)
        pooled = PooledManagerOperations(
            self.jobs, {(1, "impl"): operations},
            resolved_principals=resolved)
        with self.assertRaises(ContractRefusal):
            pooled.admit(attempt, job_of(self.jobs, "one"))
        allocation = allocation_of(self.jobs, attempt["attempt_id"])
        self.assertEqual(allocation["allocation_state"], "recovery-required")
        # AND THE CAPACITY IS STILL OUT OF CIRCULATION, which is the point: a
        # second stage may not take this worker while that offer might yet be
        # accepted.
        submit(self.jobs, submission("sub-2", jobs=[
            job("two", stages=[stage("implementation", "work:two")])]))
        second = self.attempting(self.jobs, "two/implementation")
        with self.assertRaises(ContractRefusal):
            reserve(self.jobs, second)

    # -- [P2] a historical variant activates again --------------------------

    def test_returning_to_a_historical_variant_is_a_new_generation(self):
        primary = self.one_worker_pool("primary")
        fallback = self.one_worker_pool("fallback")
        resolved = principals(primary)
        self.assertEqual(self.activate(primary, resolved)["generation"], 1)
        self.assertEqual(self.activate(fallback, resolved)["generation"], 2)
        returned = self.activate(primary, resolved)
        self.assertEqual(returned["generation"], 3)
        self.assertEqual(returned["variant"], "primary")
        self.assertEqual(scheduler.active_generation(
            self.jobs)["generation"], 3)
        # AN EXACT RETRY OF THE LIVE ACTIVATION IS STILL ONE ACT.
        self.assertEqual(self.activate(primary, resolved), returned)
        self.assertEqual(scheduler.active_generation(
            self.jobs)["generation"], 3)

    def test_the_active_generation_survives_a_reopen(self):
        primary = self.one_worker_pool("primary")
        fallback = self.one_worker_pool("fallback")
        resolved = principals(primary)
        self.activate(primary, resolved)
        self.activate(fallback, resolved)
        self.activate(primary, resolved)
        self.jobs.close()
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-reopened",
                                 clock=self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(scheduler.active_generation(
            reopened)["generation"], 3)
        self.assertEqual(scheduler.active_generation(
            reopened)["variant"], "primary")

    # -- [P2] a settled allocation still checks its operands -----------------

    def test_a_second_release_with_another_reason_refuses(self):
        document = self.one_worker_pool()
        self.activate(document, principals(document))
        attempt = self.attempts([
            job("one", stages=[stage("implementation", "work:one")])])[0]
        reserve(self.jobs, attempt)
        first = scheduler.release(self.jobs, attempt["attempt_id"], "cleanup-complete")
        self.assertEqual(first["allocation_state"], "released")
        # THE EXACT REPEAT REPLAYS.
        self.assertEqual(
            scheduler.release(self.jobs, attempt["attempt_id"],
                              "cleanup-complete"), first)
        # A CHANGED OPERAND UNDER THE SAME DERIVED IDENTITY REFUSES.
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.release(self.jobs, attempt["attempt_id"],
                              "cleanup-retained")
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertEqual(allocation_of(
            self.jobs, attempt["attempt_id"])["release_reason"],
                         "cleanup-complete")

    def test_the_two_settlement_orderings_end_differently(self):
        """Recovery-then-release settles; release-then-recovery refuses.

        The two are not symmetric and the asymmetry is the contract: a
        quarantined allocation may still be released once its evidence
        arrives, while a released one has already put its capacity back in
        circulation and quarantining it again would be quarantining whatever
        took it.

        A REPEATED recovery is a third thing and is neither: it is an exact
        replay of an act that did happen, so it answers what was recorded.
        """
        document = self.one_worker_pool()
        self.activate(document, principals(document))
        first, second, third = self.attempts([
            job("one", stages=[stage("implementation", "work:one")]),
            job("two", stages=[stage("implementation", "work:two")]),
            job("three", stages=[stage("implementation", "work:three")])])
        reserve(self.jobs, first)
        quarantined = scheduler.require_recovery(self.jobs,
                                                 first["attempt_id"])
        self.assertEqual(quarantined["allocation_state"], "recovery-required")
        released = scheduler.release(self.jobs, first["attempt_id"],
                                     "cleanup-complete")
        self.assertEqual(released["allocation_state"], "released")
        # THE REPLAY OF THE RECOVERY THAT DID HAPPEN answers what it recorded,
        # rather than re-deciding it against the later state.
        self.assertEqual(
            scheduler.require_recovery(self.jobs, first["attempt_id"]),
            quarantined)
        # THE OTHER ORDERING, on an allocation that was never quarantined.
        reserve(self.jobs, second)
        scheduler.release(self.jobs, second["attempt_id"], "cleanup-retained")
        with self.assertRaises(ContractRefusal) as caught:
            scheduler.require_recovery(self.jobs, second["attempt_id"])
        self.assertIn("released", caught.exception.message)
        # The freed capacity really is usable, which is what "released" meant.
        self.assertEqual(reserve(self.jobs, third)["worker_id"], "impl")


class FourEffectiveClaimsAreLiveTogether(PoolCase):
    """W71877 review acceptance gap: the four-capacity proof stopped at
    `reserve`.

    Reservations are the SCHEDULER's answer about capacity. The accepted claim
    is Authority's, and `fixtures.FakeSession.claim_slots` exists to mimic its
    one-live-claim-per-principal rule -- but nothing constructed a session with
    that map, so four simultaneous EFFECTIVE claims, the alias collapse at that
    boundary, the returned-principal binding and the routed run were all
    unproved.

    Everything here therefore goes through the real `ManagerOperations` of four
    participants sharing ONE claim-slot map, which is what makes the four
    claims a capacity statement rather than four independent fakes agreeing.
    """

    WORK = ("work:i1", "work:i2", "work:r1", "work:r2")

    def jobs_document(self):
        return [job("impl-1", stages=[stage("implementation", "work:i1")]),
                job("impl-2", stages=[stage("implementation", "work:i2")]),
                job("review-1", stages=[stage("review", "work:r1")]),
                job("review-2", stages=[stage("review", "work:r2")])]

    def pooled(self, document, resolved, slots):
        """One pooled surface over four real participant-bound operations.

        ONE CONTROL STORE AND ONE CLAIM-SLOT MAP, because both are what the
        four workers actually share in a deployment: the manager's own store,
        and Authority's per-principal claim slot. Four private copies of either
        would let this case pass while the property it is about was false.
        """
        control = self.control()
        self.sessions = {}
        self.started = {}
        operations = {}
        for entry in document["workers"]:
            session = FakeSession(entry["participant"],
                                  principal=resolved[entry["participant"]],
                                  claim_slots=slots)
            for work_id in self.WORK:
                session.open_work(work_id)
            self.sessions[entry["worker_id"]] = session
            # ONE RECORDING RUNTIME START PER WORKER, which is what makes the
            # launch pass a statement about ROUTING. A single shared recorder
            # would say four stages started and nothing about which endpoint
            # started each.
            operations[(1, entry["worker_id"])] = self.operations(
                control=control,
                port=AuthorityPort(session, fake_claim_signature),
                start_runtime=self.starting(entry["worker_id"]))
        self.control_store = control
        return PooledManagerOperations(self.jobs, operations,
                                       resolved_principals=resolved)

    def starting(self, worker_id):
        def start(stage, job):
            self.started.setdefault(worker_id, []).append(stage["stage_id"])
            return {"runtime_id": f"runtime-{worker_id}-{stage['stage_id']}"}
        return start

    def accept_every_offer(self, pooled):
        """Accept each issued offer as its own worker, by its own bearer.

        The offers are issued by `admit` during the first tick; a claim is
        owed only once the offer this manager delivered has been accepted, so
        without this step every claim defers forever and the case would prove
        that deferral rather than the claim boundary.
        """
        for issued in list(self.delivered):
            attempt = [row for row in allocation_rows(self.jobs)
                       if row["assignment_id"] == issued["runtime_attempt_id"]]
            self.assertEqual(len(attempt), 1, issued)
            worker = pooled.workers[(attempt[0]["generation"],
                                     attempt[0]["worker_id"])]
            accept_offer(self.control_store, worker.port,
                         offer_id=issued["offer_id"], decision="accept",
                         bearer=issued["bearer"], now=NOW,
                         runtime_attempt_id=issued["runtime_attempt_id"],
                         work_ref={"authority_uuid": UUID,
                                   "work_id": issued["work_id"]})

    def test_four_distinct_principals_hold_four_live_claims(self):
        document = pool()
        resolved = principals(document)
        self.activate(document, resolved)
        submit(self.jobs, submission(jobs=self.jobs_document()))
        slots = {}
        pooled = self.pooled(document, resolved, slots)
        sweep(self.jobs, pooled, now=NOW)
        self.accept_every_offer(pooled)
        report = sweep(self.jobs, pooled, now=NOW)
        self.assertEqual(sorted(act["outcome"] for act in report["acts"]),
                         ["performed"] * 4)
        # FOUR EFFECTIVE CLAIMS, held at the Authority-like boundary itself:
        # the slot map is what refuses a second live claim per principal, and
        # it now holds one work per principal rather than one per participant.
        self.assertEqual(len(slots), 4)
        self.assertEqual(sorted(slots), sorted(
            resolved[entry["participant"]] for entry in document["workers"]))
        self.assertEqual(sorted(slots.values()), sorted(self.WORK))
        # AND EACH CLAIM WENT THROUGH ITS RESERVED WORKER. The allocation says
        # which participant owns the stage; the session that recorded the claim
        # says which one actually acted.
        for row in allocation_rows(self.jobs):
            with self.subTest(stage=row["stage_id"]):
                session = self.sessions[row["worker_id"]]
                claimed = [call for call in session.calls
                           if call[0] == "claim"]
                self.assertEqual(len(claimed), 1)
                self.assertEqual(claimed[0][1]["work_id"],
                                 self.work_of(row["stage_id"]))
                self.assertEqual(row["allocation_state"], "reserved")
        # AND EACH CLAIMED STAGE RAN THROUGH THAT SAME WORKER. The claim proves
        # the capacity; the launch is what proves the routing survives to the
        # act, which is the boundary the previous review asked for and the one
        # a fixture that stops at `claim` cannot reach.
        #
        # THE SAME TICK, because the launch pass is last and reacquires state
        # first: a stage this tick claimed is a stage this tick starts. Asking
        # for another sweep would start each one a second time and prove only
        # that a started stage starts again.
        self.assertEqual(sorted(one["outcome"] for one in report["started"]),
                         ["started"] * 4)
        for row in allocation_rows(self.jobs):
            with self.subTest(launched=row["stage_id"]):
                self.assertEqual(self.started.get(row["worker_id"]),
                                 [row["stage_id"]])
        self.assertEqual(sum(len(one) for one in self.started.values()), 4)

    def work_of(self, stage_id):
        """This suite's own stage-to-Work mapping, written once."""
        job_id = stage_id.split("/")[0]
        return {"impl-1": "work:i1", "impl-2": "work:i2",
                "review-1": "work:r1", "review-2": "work:r2"}[job_id]

    def test_two_participants_on_one_principal_collapse_at_the_seam(self):
        """The alias collapse driven through the scheduler, in the shape that
        makes it a question.

        SUPERSEDED SHAPE: my first version called two `FakeSession.claim`
        methods directly. That proves the fake refuses and says nothing about
        this Work -- the scheduler was never in the path, so its claim that it
        cannot tell the aliases apart was not exercised at all.

        AND THE PREMISE OF THAT CLAIM TURNS OUT TO BE FALSE, which is the more
        useful result. Driving the intended two-generation shape shows the
        scheduler's live-principal uniqueness is CROSS-GENERATION: the second
        alias is refused at `reserve`, before any offer or claim exists, so
        two participants that Authority maps to one principal never become two
        capacities in the first place. That is the collapse, and it happens
        one layer earlier than the previous framing assumed.

        The Authority slot is still the backstop for what the scheduler cannot
        see -- a principal that changes under a live allocation -- and
        `ClaimBinding.test_claim_principal_mismatch_quarantines_the_allocation`
        is where that is proved.
        """
        first_pool = pool("primary", workers=[worker(
            "alias-a", "implementation", "baton.alias-a", ["implementation"])])
        second_pool = pool("fallback", workers=[worker(
            "alias-b", "implementation", "baton.alias-b", ["implementation"])])
        self.activate(first_pool, {"baton.alias-a": "principal:one"})
        submit(self.jobs, submission(jobs=[
            job("one", stages=[stage("implementation", "work:i1")])]))
        held = self.attempting(self.jobs, "one/implementation")
        reserve(self.jobs, held)
        self.activate(second_pool, {"baton.alias-b": "principal:one"})
        submit(self.jobs, submission("sub-2", jobs=[
            job("two", stages=[stage("implementation", "work:i2")])]))
        other = self.attempting(self.jobs, "two/implementation")
        with self.assertRaises(ContractRefusal) as caught:
            reserve(self.jobs, other)
        self.assertEqual(caught.exception.code, "precondition")
        # ONE ALLOCATION, ACROSS TWO GENERATIONS, for one canonical principal.
        rows = allocation_rows(self.jobs)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["canonical_principal"], "principal:one")
        self.assertEqual(rows[0]["generation"], 1)
        # AND THE UNRESERVED ALIAS CANNOT REACH A WORKER THROUGH THE SEAM
        # EITHER. There is no second capacity, so there is no second endpoint:
        # the pooled surface refuses the stage by name rather than routing it
        # to the alias that happens to be in the active generation.
        control = self.control()
        attached = {}
        for generation, worker_id, participant in (
                (1, "alias-a", "baton.alias-a"),
                (2, "alias-b", "baton.alias-b")):
            session = FakeSession(participant, principal="principal:one")
            for work_id in self.WORK:
                session.open_work(work_id)
            attached[(generation, worker_id)] = self.operations(
                control=control,
                port=AuthorityPort(session, fake_claim_signature))
        pooled = PooledManagerOperations(
            self.jobs, attached,
            resolved_principals={"baton.alias-a": "principal:one",
                                 "baton.alias-b": "principal:one"})
        with self.assertRaises(ContractRefusal) as refused:
            pooled.claim(other)
        self.assertIn("no scheduler allocation", refused.exception.message)

    def test_one_worker_failing_to_claim_settles_only_its_own_slot(self):
        """Failure isolation AND the settlement the scheduler owes for it.

        SUPERSEDED SHAPE: my first version asserted that three claims performed
        and that their allocations were still reserved. It would have passed
        while the fourth capacity leaked, which is the state the settlement
        table exists to prevent -- so the refused slot is advanced through
        canonical observation and its exact end state is asserted.

        WHAT THAT STATE ACTUALLY IS: retained. A durable claim refusal is not
        an ending. The offer stays live, the episode owes its claim, the sweep
        defers it every tick, and the allocation stays `reserved` -- so the
        capacity is held rather than released, which is what the settlement
        table asks for when nothing has proved that no assignment exists. The
        assertion below is that it is held and NOT reusable, because "released"
        and "leaked" look identical from a row and differ entirely from the
        next stage's point of view.
        """
        document = pool()
        resolved = principals(document)
        self.activate(document, resolved)
        submit(self.jobs, submission(jobs=self.jobs_document()))
        pooled = self.pooled(document, resolved, {})
        sweep(self.jobs, pooled, now=NOW)
        self.accept_every_offer(pooled)
        broken = self.sessions["review-b"]
        broken.claim_answer = ContractRefusal(
            "refused", "precondition", "this participant cannot claim",
            durable=True)
        report = sweep(self.jobs, pooled, now=NOW)
        outcomes = sorted(act["outcome"] for act in report["acts"])
        self.assertEqual(outcomes.count("performed"), 3)
        self.assertEqual(outcomes.count("deferred"), 1)
        # THE OTHER THREE ARE UNTOUCHED, and each of them launched through its
        # own reserved worker.
        live = {row["worker_id"]: row["allocation_state"]
                for row in allocation_rows(self.jobs)}
        for worker_id in ("impl-a", "impl-b", "review-a"):
            with self.subTest(worker=worker_id):
                self.assertEqual(live[worker_id], "reserved")
                self.assertEqual(len(self.started.get(worker_id, [])), 1)
        self.assertNotIn("review-b", self.started)
        # THE FAILED SLOT IS ADVANCED THROUGH CANONICAL OBSERVATION rather than
        # settled from the refusal itself, which is the rule the settlement
        # table states: further ticks observe, reconcile and re-derive.
        for _ in range(3):
            again = sweep(self.jobs, pooled, now=NOW)
            self.assertEqual([act["outcome"] for act in again["acts"]],
                             ["deferred"])
        self.assertIsNotNone(episodes.live_of(self.jobs, "review-2/review"))
        self.assertEqual(live["review-b"], "reserved")
        self.assertEqual(
            {row["worker_id"]: row["allocation_state"]
             for row in allocation_rows(self.jobs)}["review-b"], "reserved")
        # AND RETAINED IS NOT LEAKED: nothing else may take that capacity while
        # its offer may still be claimed.
        submit(self.jobs, submission("sub-2", jobs=[
            job("review-3", stages=[stage("review", "work:r3")])]))
        third = self.attempting(self.jobs, "review-3/review")
        with self.assertRaises(ContractRefusal) as caught:
            reserve(self.jobs, third)
        self.assertEqual(caught.exception.code, "precondition")


class PoolComposition(PoolCase):

    def test_sweep_reserves_before_issuing_each_offer(self):
        document = pool(workers=[
            worker("impl-a", "implementation", "baton.impl-a",
                   ["implementation"]),
            worker("impl-b", "implementation", "baton.impl-b",
                   ["implementation"])])
        resolved = principals(document)
        self.activate(document, resolved)
        submit(self.jobs, submission(jobs=[
            job("one", stages=[stage("implementation", "work:one")]),
            job("two", stages=[stage("implementation", "work:two")])]))
        control = self.control()
        operations = {}
        for entry in document["workers"]:
            session = FakeSession(entry["participant"],
                                  principal=resolved[entry["participant"]])
            session.open_work("work:one")
            session.open_work("work:two")
            operations[(1, entry["worker_id"])] = self.operations(
                control=control,
                port=AuthorityPort(session, fake_claim_signature))
        pooled = PooledManagerOperations(self.jobs, operations,
                                         resolved_principals=resolved)
        json.dumps(pooled.recover(now=NOW))
        report = sweep(self.jobs, pooled, now=NOW)
        self.assertEqual([act["outcome"] for act in report["acts"]],
                         ["performed", "performed"])
        allocations = allocation_rows(self.jobs)
        self.assertEqual(len(allocations), 2)
        self.assertEqual({one["participant"] for one in allocations},
                         {"baton.impl-a", "baton.impl-b"})

    def test_live_allocation_keeps_its_generation_after_pool_change(self):
        original = pool(workers=[worker(
            "old", "implementation", "baton.old", ["implementation"])])
        self.activate(original, {"baton.old": "principal:old"})
        old_attempt = self.attempts([
            job("old", stages=[stage("implementation", "work:old")])])[0]
        reserve(self.jobs, old_attempt)
        replacement = pool("replacement", workers=[worker(
            "new", "implementation", "baton.new", ["implementation"])])
        self.activate(replacement, {"baton.new": "principal:new"})
        submit(self.jobs, submission("sub-2", jobs=[
            job("new", stages=[stage("implementation", "work:new")])]))
        new_attempt = self.attempting(self.jobs, "new/implementation")
        reserve(self.jobs, new_attempt)
        pooled = PooledManagerOperations(
            self.jobs,
            {(1, "old"): _ClaimingStub("baton.old", "principal:old"),
             (2, "new"): _ClaimingStub("baton.new", "principal:new")},
            resolved_principals={"baton.old": "principal:old",
                                 "baton.new": "principal:new"})
        self.assertEqual(pooled.claim(old_attempt)["decision"]["principal"],
                         "principal:old")
        self.assertEqual(pooled.claim(new_attempt)["decision"]["principal"],
                         "principal:new")

    def test_adoption_refuses_an_offer_signed_by_another_participant(self):
        document = pool(workers=[worker(
            "impl", "implementation", "baton.impl", ["implementation"])])
        self.activate(document, {"baton.impl": "principal:impl"})
        submit(self.jobs, submission(jobs=[
            job("one", stages=[stage("implementation", "work:one")])]))
        attempt = self.attempting(self.jobs, "one/implementation")
        reserve(self.jobs, attempt)
        control = self.control()
        wrong_session = FakeSession("baton.other", principal="principal:other")
        wrong_session.open_work("work:one")
        wrong = self.operations(
            control=control,
            port=AuthorityPort(wrong_session, fake_claim_signature))
        wrong.admit(attempt, job_of(self.jobs, "one"))
        right_session = FakeSession("baton.impl", principal="principal:impl")
        right_session.open_work("work:one")
        pooled = PooledManagerOperations(
            self.jobs,
            {(1, "impl"): self.operations(
                control=control,
                port=AuthorityPort(right_session, fake_claim_signature))},
            resolved_principals={"baton.impl": "principal:impl"})
        with self.assertRaises(ContractRefusal) as caught:
            check_binding(pooled, attempt, job_of(self.jobs, "one"))
        self.assertEqual(caught.exception.code, "operation-collision")


if __name__ == "__main__":
    import unittest
    unittest.main()
