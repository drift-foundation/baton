"""W156162: the per-Job execution ceilings, their persistence and their reads.

WHAT THE OWNER DECIDED, and therefore what these cases hold this build to
(`work/records/2026/09/finding-v12-per-job-budgets/FINDING.md`,
2026-09-13T00:49:46Z): a Job may override the provider turn and the verification
command ceilings, Job-wide; an omitted setting keeps that runner's EXISTING
default; cumulative accounting and role/stage pools are deferred; units, scope
and effective values are exposed; and there is no universal five-minute default.

WHAT IS DELIBERATELY NOT ASSERTED HERE. Nothing in this module claims a provider
turn or a verification command actually RAN with a configured ceiling. That is
the delivery half of the plan -- the launch envelope and the runner readers --
and it is not in this slice. Configuration alone is not evidence that a command
ran, and a test pretending otherwise would be the exact confusion this Work
exists to remove.
"""

import json
import os
import shutil
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, documents, submit
from baton_v12.job_manager import execution_limits as limits
from baton_v12.job_manager import projection, schema, submission as rows

from .fixtures import JobManagerCase, NOW, UUID, job, stage, submission


def limited(**settings):
    """A /2 submission whose one Job states exactly these settings."""
    held = job("job-a", stages=[stage()])
    held["execution_limits"] = dict(settings)
    return {"schema": documents.SUBMISSION_SCHEMA,
            "submission_id": "sub-1", "jobs": [held]}


class TheSettingsAreOwnedBeforeAnythingIsStored(unittest.TestCase):
    """The document owner, alone: a ceiling nobody can honour is refused where
    it is written rather than carried to a runner that must guess."""

    def test_a_job_that_states_nothing_keeps_every_runner_default(self):
        held = limits.resolved(None)
        self.assertEqual(
            {name: one["seconds"]
             for name, one in held["boundaries"].items()},
            {"provider_turn": 3600, "ordinary_verification": 900,
             "integration_verification": 1800, "host_verification": 300})
        self.assertEqual({one["origin"] for one in held["boundaries"].values()},
                         {limits.COMPATIBILITY})
        self.assertEqual(held["requested"], {})

    def test_the_units_and_the_scope_travel_with_the_numbers(self):
        """The requirement exists because a number alone was read as something
        it was not. Seconds, per invocation, said rather than assumed."""
        held = limits.resolved({"provider_turn_seconds": 60})
        self.assertEqual(held["units"], "seconds")
        self.assertEqual(held["scope"], "per-invocation")
        self.assertEqual(held["boundaries"]["provider_turn"]["seconds"], 60)
        self.assertEqual(held["boundaries"]["provider_turn"]["origin"],
                         limits.JOB)
        # AND THE DEFAULT IS STILL VISIBLE BESIDE THE OVERRIDE, so a reader can
        # see what was moved rather than only where it landed.
        self.assertEqual(
            held["boundaries"]["provider_turn"]["default_seconds"], 3600)

    def test_one_verification_setting_reaches_all_three_boundaries(self):
        """Job-wide overrides, which is what the owner selected. A Job that
        wants the ordinary and the imported verification to differ is asking
        for the deferred role pools, and cannot half-express it here."""
        held = limits.resolved({"verification_command_seconds": 120})
        for boundary in ("ordinary_verification", "integration_verification",
                         "host_verification"):
            with self.subTest(boundary=boundary):
                self.assertEqual(held["boundaries"][boundary]["seconds"], 120)
                self.assertEqual(held["boundaries"][boundary]["origin"],
                                 limits.JOB)
        # AND THE PROVIDER TURN IS UNTOUCHED BY IT.
        self.assertEqual(held["boundaries"]["provider_turn"]["seconds"], 3600)
        self.assertEqual(held["boundaries"]["provider_turn"]["origin"],
                         limits.COMPATIBILITY)

    def test_each_field_alone_and_both_together(self):
        alone = limits.resolved({"provider_turn_seconds": 30})
        self.assertEqual(alone["boundaries"]["ordinary_verification"]["origin"],
                         limits.COMPATIBILITY)
        both = limits.resolved({"provider_turn_seconds": 30,
                                "verification_command_seconds": 45})
        self.assertEqual(both["boundaries"]["provider_turn"]["seconds"], 30)
        self.assertEqual(
            both["boundaries"]["host_verification"]["seconds"], 45)
        self.assertEqual(both["requested"],
                         {"provider_turn_seconds": 30,
                          "verification_command_seconds": 45})

    def test_an_empty_object_is_a_job_that_decided_nothing(self):
        """Admitted as itself: the member was opened and no setting made. It
        resolves exactly as absence does, and is a different document."""
        self.assertEqual(limits.owned_execution_limits({}), {})
        self.assertIsNone(limits.owned_execution_limits(None))

    def refused(self, value):
        with self.assertRaises(ContractRefusal) as caught:
            limits.owned_execution_limits(value)
        return caught.exception

    def test_a_boolean_is_not_a_number_of_seconds(self):
        """`True` is an `int` in Python and would otherwise persist as one
        second -- a ceiling nobody wrote."""
        held = self.refused({"provider_turn_seconds": True})
        self.assertIn("whole number of seconds", held.message)

    def test_a_fraction_is_refused_rather_than_rounded(self):
        self.refused({"provider_turn_seconds": 900.5})

    def test_zero_and_negative_seconds_are_refused(self):
        for value in (0, -1):
            with self.subTest(value=value):
                self.refused({"verification_command_seconds": value})

    def test_a_value_outside_the_supported_range_is_refused_not_clamped(self):
        """ONE range, shared by every reader, and no silent clamp: a runner
        handed a ceiling different from the one written is the confusion this
        Work removes."""
        held = self.refused({"provider_turn_seconds": limits.MAX_SECONDS + 1})
        self.assertIn("refused here rather than clamped", held.message)
        self.assertEqual(
            limits.owned_execution_limits(
                {"provider_turn_seconds": limits.MAX_SECONDS}),
            {"provider_turn_seconds": limits.MAX_SECONDS})
        self.assertEqual(
            limits.owned_execution_limits(
                {"provider_turn_seconds": limits.MIN_SECONDS}),
            {"provider_turn_seconds": limits.MIN_SECONDS})

    def test_an_unknown_setting_is_refused(self):
        self.refused({"cumulative_seconds": 300})

    def test_a_string_is_not_a_document(self):
        self.refused("900")


class TheSubmissionCarriesThemOnlyWhereItsVersionSaysSo(unittest.TestCase):
    """Two versions, both read. /1 is preserved exactly, which is what makes
    the compatibility promise a promise rather than a migration."""

    def test_a_version_one_submission_is_still_accepted_unchanged(self):
        held = documents.owned_submission(submission())
        self.assertEqual(held["schema"], "baton.v12.job-submission/1")
        for one in held["jobs"]:
            self.assertNotIn("execution_limits", one)

    def test_a_version_one_job_carrying_limits_is_refused(self):
        """The member is admitted by the version that NAMES it. A /1 document
        growing it is refused as the unknown member it is there."""
        document = submission()
        document["jobs"][0]["execution_limits"] = {"provider_turn_seconds": 60}
        with self.assertRaises(ContractRefusal):
            documents.owned_submission(document)

    def test_a_version_two_job_carries_its_settings(self):
        held = documents.owned_submission(limited(provider_turn_seconds=60))
        self.assertEqual(held["schema"], "baton.v12.job-submission/2")
        self.assertEqual(held["jobs"][0]["execution_limits"],
                         {"provider_turn_seconds": 60})

    def test_a_present_null_is_not_the_optional_object(self):
        """Review 2026-09-13T01:13:49Z R2: `execution_limits: null` was admitted
        and preserved as normalized intent, because the internal
        omission convenience was reached for a member the document really
        carried. Omit it, or give an object -- the empty one included."""
        document = limited()
        document["jobs"][0]["execution_limits"] = None
        with self.assertRaises(ContractRefusal) as caught:
            documents.owned_submission(document)
        self.assertIn("omitted entirely", caught.exception.message)
        # AND THE INTERNAL ABSENCE HANDLING IS UNTOUCHED.
        self.assertIsNone(limits.owned_execution_limits(None))

    def test_a_version_two_job_may_still_state_nothing(self):
        document = limited()
        del document["jobs"][0]["execution_limits"]
        held = documents.owned_submission(document)
        self.assertNotIn("execution_limits", held["jobs"][0])

    def test_the_normalized_document_keeps_its_own_version(self):
        """The canonical text is the durable identity a resubmission is
        compared against, so rewriting a /1 caller's document as /2 would give
        one intent two identities -- and would make an old signed operation
        unreplayable after this build shipped."""
        self.assertEqual(
            documents.owned_submission(submission())["schema"],
            "baton.v12.job-submission/1")

    def test_an_unknown_submission_version_is_refused(self):
        document = limited()
        document["schema"] = "baton.v12.job-submission/9"
        with self.assertRaises(ContractRefusal) as caught:
            documents.owned_submission(document)
        self.assertIn("job-submission/2", caught.exception.message)


class TheStoreKeepsWhatTheJobAskedFor(JobManagerCase):
    """Persistence, replay, conflict and the read-only status, over the real
    store and the real submission owner."""

    def store(self, incarnation="jobs-1"):
        held = JobStore.open(self.job_path, authority_uuid=UUID,
                             incarnation=incarnation, clock=self.clock)
        self.addCleanup(held.close)
        return held

    def test_a_configured_job_stores_its_intent_and_an_absent_one_stores_none(
            self):
        store = self.store()
        document = limited(provider_turn_seconds=60,
                           verification_command_seconds=45)
        document["jobs"].append(job("job-b", stages=[stage()]))
        submit(store, document)
        self.assertEqual(
            rows.execution_limits_of(store, "job-a"),
            {"requested": {"provider_turn_seconds": 60,
                           "verification_command_seconds": 45},
             "compatibility_generation": limits.CURRENT_GENERATION})
        # AND A JOB THAT CONFIGURED NOTHING STILL PINS ITS GENERATION, because
        # the preserved defaults are as much a part of its admitted
        # configuration as an override is.
        self.assertEqual(
            rows.execution_limits_of(store, "job-b"),
            {"requested": {},
             "compatibility_generation": limits.CURRENT_GENERATION})

    def test_an_exact_replay_keeps_the_settings_and_writes_nothing_new(self):
        store = self.store()
        document = limited(provider_turn_seconds=60)
        first = submit(store, document)
        again = submit(store, document)
        self.assertEqual(first, again)
        self.assertEqual(
            rows.execution_limits_of(store, "job-a")["requested"],
            {"provider_turn_seconds": 60})
        self.assertEqual(
            store._connection.execute(
                "SELECT COUNT(*) FROM job_execution_limits").fetchone()[0], 1)

    def test_the_same_submission_with_changed_settings_conflicts(self):
        """Defaults changing cannot reinterpret an existing Job, and neither
        can a caller resubmitting one identity with another ceiling."""
        store = self.store()
        submit(store, limited(provider_turn_seconds=60))
        with self.assertRaises(ContractRefusal):
            submit(store, limited(provider_turn_seconds=61))
        self.assertEqual(
            rows.execution_limits_of(store, "job-a")["requested"],
            {"provider_turn_seconds": 60})

    def test_a_version_one_job_resolves_to_every_preserved_default(self):
        store = self.store()
        submit(store, submission())
        admitted = rows.execution_limits_of(store, "job-a")
        held = limits.resolved(admitted["requested"],
                               admitted["compatibility_generation"])
        self.assertEqual(
            {name: one["seconds"]
             for name, one in held["boundaries"].items()},
            {"provider_turn": 3600, "ordinary_verification": 900,
             "integration_verification": 1800, "host_verification": 300})

    def test_the_public_status_reports_requested_and_effective_values(self):
        store = self.store()
        submit(store, limited(verification_command_seconds=120))
        held = projection.status(store, self.operations(),
                                 observed_at=NOW)
        self.assertEqual(held["schema"], "baton.v12.job-status/5")
        [entry] = [one for one in held["jobs"] if one["job_id"] == "job-a"]
        answer = entry["execution_limits"]
        self.assertEqual(answer["requested"],
                         {"verification_command_seconds": 120})
        self.assertEqual(answer["units"], "seconds")
        self.assertEqual(answer["scope"], "per-invocation")
        self.assertEqual(
            answer["boundaries"]["ordinary_verification"]["seconds"], 120)
        self.assertEqual(answer["boundaries"]["provider_turn"]["seconds"],
                         3600)
        self.assertEqual(answer["boundaries"]["provider_turn"]["origin"],
                         "compatibility")

    def test_repeated_read_only_status_changes_nothing(self):
        store = self.store()
        submit(store, limited(provider_turn_seconds=60))
        operations = self.operations()
        before = self.digest_of(self.job_path)
        first = projection.status(store, operations, observed_at=NOW)
        second = projection.status(store, operations, observed_at=NOW)
        self.assertEqual(first, second)
        self.assertEqual(self.digest_of(self.job_path), before)

    def digest_of(self, path):
        import hashlib

        with open(path, "rb") as reading:
            return hashlib.sha256(reading.read()).hexdigest()


class TheJobOwnerComposesItsOwnLaunchContext(JobManagerCase):
    """PLAN item 3: resolve through the immutable public Job reader at launch
    preparation.

    Deciding WHICH configuration a container is running belongs to the Job's own
    owner; a Worker Manager composing it from parts would be a second party
    resolving a Job's configuration. What this class does NOT show is that any
    launch actually carries it -- the call sites are named in PROGRESS and are
    not written yet.
    """

    def store(self):
        held = JobStore.open(self.job_path, authority_uuid=UUID,
                             incarnation="jobs-1", clock=self.clock)
        self.addCleanup(held.close)
        return held

    def context(self, store, **changed):
        held = {"attempt_id": "attempt-1",
                "runtime_input_digest": "sha256:" + "9" * 64,
                "runtime_policy_digest": "sha256:" + "2" * 64}
        held.update(changed)
        return rows.job_execution_context(store, "job-a", **held)

    def test_the_context_carries_the_jobs_own_admitted_configuration(self):
        store = self.store()
        submit(store, limited(provider_turn_seconds=60))
        held = self.context(store)
        self.assertEqual(held["job_id"], "job-a")
        self.assertEqual(held["attempt_id"], "attempt-1")
        self.assertEqual(
            held["execution_limits"]["boundaries"]["provider_turn"]["seconds"],
            60)
        self.assertEqual(
            held["execution_limits"]["compatibility_generation"],
            limits.CURRENT_GENERATION)

    def test_the_job_and_runtime_identities_are_both_stated(self):
        """They are different facts: a review or a derived judgment runs over a
        frozen input that is not the Job's own, so the runtime's identities are
        the caller's to supply and are carried rather than compared."""
        store = self.store()
        submit(store, limited())
        held = self.context(store)
        self.assertEqual(held["job_input_digest"],
                         "sha256:" + "1" * 64)
        self.assertEqual(held["runtime_input_digest"],
                         "sha256:" + "9" * 64)
        self.assertNotEqual(held["job_input_digest"],
                            held["runtime_input_digest"])

    def test_the_context_the_owner_composes_is_the_one_the_carrier_accepts(
            self):
        """The two halves meet: what this owner composes is exactly what the
        launch carrier will admit, seal and adopt -- which is the point of
        having one party resolve it."""
        from baton_v12.worker_manager import launch

        store = self.store()
        submit(store, limited(verification_command_seconds=45))
        held = self.context(store)
        document = launch.launch_document(session="s", contract="c", role="r",
                                          job_execution=held)
        self.assertEqual(document["schema"], "baton.worker-launch/3")
        self.assertEqual(document["job_execution"], held)

    def test_a_legacy_job_composes_a_generation_zero_context(self):
        store = self.store()
        submit(store, submission())
        store._connection.execute("DELETE FROM job_execution_limits")
        held = self.context(store)
        self.assertEqual(
            held["execution_limits"]["compatibility_generation"],
            limits.LEGACY_GENERATION)
        self.assertEqual(
            held["execution_limits"]["boundaries"]["provider_turn"]["seconds"],
            3600)

    def test_the_owner_invents_no_runtime_identity(self):
        store = self.store()
        submit(store, limited())
        with self.assertRaises(ContractRefusal):
            self.context(store, runtime_input_digest=None)


class ANewDefaultCannotReinterpretAnAdmittedJob(JobManagerCase):
    """Review 2026-09-13T01:13:49Z R1, as its own class.

    The defect was mine and the reasoning behind it was backwards: I resolved
    against this build's constants at read time and argued that a pinned
    resolution would go stale. An admitted Job's configuration is deliberately
    STABLE -- that is what PLAN item 1 says -- and the reviewer's probe showed
    the consequence exactly: a Job that preserved the provider default reported
    3600, and the same unchanged Job reported a newer default the moment one
    existed, while its identical submission still replayed.
    """

    def store(self):
        held = JobStore.open(self.job_path, authority_uuid=UUID,
                             incarnation="jobs-1", clock=self.clock)
        self.addCleanup(held.close)
        return held

    def newer_defaults(self, **changed):
        """A LATER compatibility generation, added the way a real one would be.

        Added, never edited: an edited generation is precisely the
        reinterpretation this structure exists to prevent, so the case that
        proves the rule may not break it to set itself up.
        """
        generation = max(limits.GENERATIONS) + 1
        limits.GENERATIONS[generation] = dict(
            limits.GENERATIONS[limits.CURRENT_GENERATION], **changed)
        previous = limits.CURRENT_GENERATION
        limits.CURRENT_GENERATION = generation

        def restore():
            limits.CURRENT_GENERATION = previous
            del limits.GENERATIONS[generation]

        self.addCleanup(restore)
        return generation

    def effective(self, store, job_id="job-a"):
        admitted = rows.execution_limits_of(store, job_id)
        return limits.resolved(admitted["requested"],
                               admitted["compatibility_generation"])

    def test_the_probe_that_found_this_now_answers_the_admitted_value(self):
        """The reviewer's four steps, in order, with the outcome corrected."""
        store = self.store()
        submit(store, limited(verification_command_seconds=120))
        self.assertEqual(
            self.effective(store)["boundaries"]["provider_turn"]["seconds"],
            3600)
        self.newer_defaults(provider_turn=7200)
        # THE UNCHANGED JOB STILL REPORTS WHAT IT WAS ADMITTED WITH.
        self.assertEqual(
            self.effective(store)["boundaries"]["provider_turn"]["seconds"],
            3600)
        self.assertEqual(self.effective(store)["compatibility_generation"], 1)
        # AND ITS IDENTICAL SUBMISSION STILL REPLAYS, unchanged.
        submit(store, limited(verification_command_seconds=120))
        self.assertEqual(
            self.effective(store)["boundaries"]["provider_turn"]["seconds"],
            3600)

    def test_a_new_job_gets_the_new_default_and_the_old_one_does_not(self):
        store = self.store()
        submit(store, limited(verification_command_seconds=120))
        generation = self.newer_defaults(provider_turn=7200)
        document = limited(verification_command_seconds=120)
        document["submission_id"] = "sub-2"
        document["jobs"][0]["job_id"] = "job-later"
        submit(store, document)
        self.assertEqual(
            self.effective(store, "job-later")
            ["boundaries"]["provider_turn"]["seconds"], 7200)
        self.assertEqual(
            self.effective(store, "job-later")["compatibility_generation"],
            generation)
        self.assertEqual(
            self.effective(store)["boundaries"]["provider_turn"]["seconds"],
            3600)

    def test_the_admitted_resolution_survives_a_restart(self):
        store = self.store()
        submit(store, limited(verification_command_seconds=120))
        self.newer_defaults(provider_turn=7200)
        store.close()
        reopened = JobStore.open(self.job_path, authority_uuid=UUID,
                                 incarnation="jobs-restarted",
                                 clock=self.clock)
        self.addCleanup(reopened.close)
        self.assertEqual(
            self.effective(reopened)["boundaries"]["provider_turn"]["seconds"],
            3600)

    def test_the_public_status_reports_the_admitted_generation(self):
        store = self.store()
        submit(store, limited(provider_turn_seconds=60))
        self.newer_defaults(provider_turn=7200)
        held = projection.status(store, self.operations(), observed_at=NOW)
        [entry] = [one for one in held["jobs"] if one["job_id"] == "job-a"]
        answer = entry["execution_limits"]
        self.assertEqual(answer["compatibility_generation"], 1)
        self.assertEqual(
            answer["boundaries"]["ordinary_verification"]["seconds"], 900)
        self.assertEqual(
            answer["boundaries"]["ordinary_verification"]["default_seconds"],
            900)

    def test_a_generation_this_build_does_not_hold_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            limits.resolved({}, 99)
        self.assertIn("cannot reproduce", caught.exception.message)


class TheMigrationLeavesOldJobsMeaningExactlyWhatTheyMeant(JobManagerCase):
    """A schema-4 store opened by this build gains the table and nothing else:
    its Jobs configured nothing, and an empty table is precisely that."""

    def schema_four(self):
        """A store built at the previous version, without this build's table.

        Built from THIS build's own DDL less the object the 4 -> 5 step
        creates, so the fixture cannot drift from the schema it claims to be.
        """
        from baton_v12.job_manager.store import _statements

        connection = sqlite3.connect(self.job_path, isolation_level=None)
        try:
            # A STATEMENT CARRIES ITS OWN LEADING COMMENTS, so the verb is
            # not always the first word. The table this build's 4 -> 5 step
            # creates is named, and everything else is installed unchanged.
            for statement in _statements(schema.SCHEMA):
                if any(created in statement for created in (
                        "CREATE TABLE job_execution_limits",
                        "CREATE TABLE integration_capacity_roots",
                        "CREATE TABLE integration_capacity_members",
                        "CREATE UNIQUE INDEX capacity_one_active_member")):
                    continue
                connection.execute(statement)
            connection.execute(
                "INSERT INTO meta (key, value) VALUES ('store_kind', ?)",
                (schema.STORE_KIND,))
            connection.execute(
                "INSERT INTO meta (key, value) "
                "VALUES ('schema_version', '4')")
            connection.execute(
                "INSERT INTO meta (key, value) "
                "VALUES ('authority_uuid', ?)",
                (UUID,))
        finally:
            connection.close()

    def test_an_empty_schema_four_store_migrates(self):
        """The NARROWER evidence this case actually supplies: the migration
        runs and adds its table. It is not old-owner admission, which
        `test_a_populated_legacy_store_keeps_its_jobs_original_meaning` proves
        from a store the old owner really wrote."""
        self.schema_four()
        store = JobStore.open(self.job_path, authority_uuid=UUID,
                              incarnation="jobs-1", clock=self.clock)
        self.addCleanup(store.close)
        self.assertEqual(
            store._connection.execute(
                "SELECT value FROM meta WHERE key = 'schema_version'"
            ).fetchone()[0], str(schema.SCHEMA_VERSION))
        # THE TABLE EXISTS AND IS EMPTY, which is what "these Jobs configured
        # nothing" durably looks like.
        self.assertEqual(
            store._connection.execute(
                "SELECT COUNT(*) FROM job_execution_limits").fetchone()[0], 0)
        submit(store, submission())
        admitted = rows.execution_limits_of(store, "job-a")
        self.assertEqual(admitted["requested"], {})
        self.assertEqual(
            limits.resolved(admitted["requested"],
                            admitted["compatibility_generation"])
            ["boundaries"]["provider_turn"]["seconds"], 3600)

    # R6, review 2026-09-13T01:36:01Z: RELATIVE TO THIS TEST, not out of the
    # Python tree into the research record. The migration regression is part of
    # the product candidate; a fixture reached through
    # `work/records/...` made it depend on the whole dossier layout, which
    # AGENTS.md keeps stand-alone tests out of. The dossier copy stays as
    # history and `execution_limits_fixtures/PROVENANCE.md` says where these
    # bytes came from.
    GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "execution_limits_fixtures",
                          "golden-schema4.sqlite3")

    def populated_legacy(self):
        """A GENUINE schema-4 store the OLD owner wrote, copied into place.

        Review 2026-09-13T01:23:33Z R4, and the correction is mine. My previous
        case opened an EMPTY schema-4 store with the CURRENT owner -- which
        migrates it to 5 before anything is submitted -- so what it called an
        old-owner admission at schema 4 was an admission at schema 5, and the
        row it then deleted was a missing-row fallback rather than history. The
        test passed and the sentence about it was false.

        This is the real thing: `golden-schema4-156492.sqlite3`, produced by
        running `submit` against the COMMITTED pre-W156162 owner in an isolated
        tree, with the generator and every source digest retained beside it in
        `golden-schema4-156492.json`. Nothing in this Work's code wrote a row
        in it.
        """
        shutil.copyfile(self.GOLDEN, self.job_path)
        os.chmod(self.job_path, 0o644)

    def beside(self):
        """A plain reader, so the pre-upgrade state is read without opening the
        store through the candidate -- which would migrate it."""
        connection = sqlite3.connect(self.job_path)
        connection.row_factory = sqlite3.Row
        self.addCleanup(connection.close)
        return connection

    def test_a_populated_legacy_store_keeps_its_jobs_original_meaning(self):
        """R4: a Job and a signed submission that EXISTED before the migration.

        Asserted before the upgrade: the old version, the absent table, the
        Jobs, and the already-recorded submission operation. Asserted after: the
        new version, the same Jobs, generation 0 defaults, and the old signed
        operation replaying to the same outcome without being rewritten.
        """
        self.populated_legacy()
        before = self.beside()
        self.assertEqual(
            before.execute("SELECT value FROM meta WHERE key = ?",
                           ("schema_version",)).fetchone()[0], "4")
        self.assertEqual(
            before.execute("SELECT name FROM sqlite_master WHERE type = "
                           "'table' AND name = 'job_execution_limits'"
                           ).fetchall(), [])
        self.assertEqual(
            [row[0] for row in before.execute(
                "SELECT job_id FROM jobs ORDER BY job_id")],
            ["job-a", "job-b"])
        # THE SIGNED OPERATION THE OLD OWNER RECORDED, read as it stands.
        [recorded] = [dict(row) for row in before.execute(
            "SELECT operation_id, kind, state, result FROM operations")]
        self.assertEqual(recorded["state"], "committed")
        outcome = json.loads(recorded["result"])
        self.assertEqual(sorted(outcome["jobs"]), ["job-a", "job-b"])
        self.assertIn("job-submission/1", outcome["signature"])

        store = JobStore.open(self.job_path, authority_uuid=UUID,
                              incarnation="jobs-1", clock=self.clock)
        self.addCleanup(store.close)
        self.assertEqual(
            store._connection.execute(
                "SELECT value FROM meta WHERE key = 'schema_version'"
            ).fetchone()[0], str(schema.SCHEMA_VERSION))

        # THE JOB MEANS WHAT IT MEANT: generation 0, the four numbers it ran
        # under, and no row invented for it.
        admitted = rows.execution_limits_of(store, "job-a")
        self.assertEqual(admitted, {"requested": None,
                                    "compatibility_generation":
                                        limits.LEGACY_GENERATION})
        self.assertEqual(
            store._connection.execute(
                "SELECT COUNT(*) FROM job_execution_limits").fetchone()[0], 0)
        held = limits.resolved(admitted["requested"],
                               admitted["compatibility_generation"])
        self.assertEqual(
            {name: one["seconds"]
             for name, one in held["boundaries"].items()},
            {"provider_turn": 3600, "ordinary_verification": 900,
             "integration_verification": 1800, "host_verification": 300})
        # AND A LATER DEFAULT CANNOT MOVE IT.
        limits.GENERATIONS[99] = dict(limits.GENERATIONS[0], provider_turn=7200)
        previous = limits.CURRENT_GENERATION
        limits.CURRENT_GENERATION = 99
        self.addCleanup(limits.GENERATIONS.pop, 99)

        def restore():
            limits.CURRENT_GENERATION = previous

        self.addCleanup(restore)
        self.assertEqual(
            limits.resolved(admitted["requested"],
                            admitted["compatibility_generation"])
            ["boundaries"]["provider_turn"]["seconds"], 3600)

        # AND THE ALREADY-SIGNED OPERATION REPLAYS, unchanged and unrewritten.
        self.assertEqual(submit(store, submission()), outcome)
        self.assertEqual(rows.execution_limits_of(store, "job-a"), admitted)
        self.assertEqual(
            store._connection.execute(
                "SELECT COUNT(*) FROM job_execution_limits").fetchone()[0], 0)

    def test_a_migrated_store_then_accepts_a_configured_job(self):
        self.schema_four()
        store = JobStore.open(self.job_path, authority_uuid=UUID,
                              incarnation="jobs-1", clock=self.clock)
        self.addCleanup(store.close)
        submit(store, limited(provider_turn_seconds=75))
        self.assertEqual(
            rows.execution_limits_of(store, "job-a")["requested"],
            {"provider_turn_seconds": 75})


if __name__ == "__main__":                 # pragma: no cover
    unittest.main()
