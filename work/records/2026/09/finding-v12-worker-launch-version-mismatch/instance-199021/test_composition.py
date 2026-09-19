"""The composer's own regressions, at a FAKE boundary.

WHY THESE EXIST, in the reviewer's words: "make every required validation
failure produce a nonzero overall result and explicitly incomplete output ...
Add focused fake-boundary tests of refused configuration/submission so a future
launcher cannot mistake this exit code for validated readiness."

NO ENGINE, NO BOOTSTRAP, NO CONTAINER, NO STORE. Every case here either injects
a fake validator or calls the real one over documents this module composes; the
one engine question the composer asks is injected too. Nothing is written: the
package's retained documents are the ones the real run left.

    python3 -m unittest -v test_composition
"""

import io
import json
import os
import stat
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import compose_lifecycle as composer                        # noqa: E402


def no_engine(argv):
    """The engine question, answered without asking an engine."""
    class Answer:
        stdout = ""
        returncode = 1
    return Answer()


class Composed(unittest.TestCase):
    """One composition, with every validator accepting unless replaced."""

    def accepting(self):
        """The real validators, each wrapped so a case can replace one."""
        return dict(composer.production_validators())

    def run_main(self, validators):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch("sys.stderr", err):
            with mock.patch("sys.stdout", out):
                code = composer.main(validators=validators, write=False,
                                     run=no_engine)
        return code, json.loads(out.getvalue()), err.getvalue()


class ARefusalIsNeverAZeroExit(Composed):
    """R3. The superseded composer returned zero whenever the manifests
    existed, so `held_configuration` and `owned_submission` could both refuse
    and the run still looked like validated readiness."""

    def refusing(self, name):
        def refuse(*args, **kwargs):
            raise RuntimeError(f"{name} says no")
        validators = self.accepting()
        validators[name] = refuse
        return validators

    def test_a_refused_configuration_exits_nonzero_and_says_incomplete(self):
        code, found, err = self.run_main(
            self.refusing("stage_execution.held_configuration"))
        self.assertEqual(code, 1)
        self.assertFalse(found["complete"])
        self.assertIn("stage_execution.held_configuration", found["refused"])
        self.assertIn("INCOMPLETE", err)

    def test_a_refused_submission_exits_nonzero_and_says_incomplete(self):
        code, found, err = self.run_main(
            self.refusing("job_manager.documents.owned_submission"))
        self.assertEqual(code, 1)
        self.assertFalse(found["complete"])
        self.assertIn("job_manager.documents.owned_submission",
                      found["refused"])
        self.assertIn("INCOMPLETE", err)

    def test_a_refused_bootstrap_input_exits_nonzero(self):
        code, found, _ = self.run_main(self.refusing("bootstrap.held"))
        self.assertEqual(code, 1)
        self.assertIn("bootstrap.held", found["refused"])

    def test_a_refused_emitted_configuration_exits_nonzero(self):
        code, found, _ = self.run_main(self.refusing("bootstrap.validated"))
        self.assertEqual(code, 1)
        self.assertIn("bootstrap.validated", found["refused"])

    def test_a_refused_seal_stops_before_anything_downstream_runs(self):
        """And the ones that never ran are as absent as ones that refused.

        This is the rule the superseded composer broke in the other direction:
        it reported the refusal in its own document and exited zero anyway.
        """
        code, found, _ = self.run_main(
            self.refusing("check_manifest_structure"))
        self.assertEqual(code, 1)
        self.assertFalse(found["complete"])
        ran = {one["validator"] for one in found["validator_calls"]}
        self.assertNotIn("stage_execution.held_configuration", ran)
        self.assertNotIn("job_manager.documents.owned_submission", ran)

    def test_a_composer_that_refuses_to_compose_is_also_nonzero(self):
        def broken(*args, **kwargs):
            raise RuntimeError("bootstrap.configuration says no")
        validators = self.accepting()
        validators["bootstrap.configuration"] = broken
        code, found, _ = self.run_main(validators)
        self.assertEqual(code, 1)
        self.assertIn("bootstrap.configuration", found["refused"])

    def test_every_required_validator_accepting_is_what_zero_means(self):
        code, found, err = self.run_main(self.accepting())
        self.assertEqual(code, 0)
        self.assertTrue(found["complete"])
        self.assertEqual(found["refused"], [])
        self.assertEqual(err, "")
        ran = {one["validator"] for one in found["validator_calls"]}
        for one in composer.REQUIRED:
            self.assertIn(one, ran)


class CompletenessIsAConjunction(unittest.TestCase):
    """`complete` is every required validator accepting, not "nothing raised"."""

    def test_a_validator_that_never_ran_is_not_completeness(self):
        run = composer.Run({})
        run.steps = [{"validator": one, "result": "accepted"}
                     for one in composer.REQUIRED[:-1]]
        self.assertFalse(run.complete)

    def test_the_whole_required_set_accepting_is(self):
        run = composer.Run({})
        run.steps = [{"validator": one, "result": "accepted"}
                     for one in composer.REQUIRED]
        self.assertTrue(run.complete)

    def test_writing_makes_the_written_files_a_required_validation_too(self):
        """The defect this rule was written for: the first run of this composer
        validated its in-memory documents, answered complete, and then its own
        output loop rewrote `task.json` indented -- so the bytes on disk were
        not the ones any validator had seen, and the installed bootstrap
        refused them for a width nobody had checked."""
        run = composer.Run({})
        run.required.append(composer.AFTER_WRITING)
        run.steps = [{"validator": one, "result": "accepted"}
                     for one in composer.REQUIRED]
        self.assertFalse(run.complete)
        run.steps.append({"validator": composer.AFTER_WRITING,
                          "result": "accepted"})
        self.assertTrue(run.complete)


class OneManifestForEveryStage(Composed):
    """R2, held against the REAL check rather than a prediction of it.

    `_SingleWorker._matches` refused the review and integration workers with
    "the Job names another bootstrap input" because each role carried its own
    seal. The manifest is a fact about the JOB's input; role independence is
    carried by the members `stage_execution._independent` actually reads.
    """

    def setUp(self):
        run = composer.Run(composer.production_validators())
        self.facts, self.documents = composer.compose(
            run, facts=composer.measured(run=no_engine), write=False)
        self.assertTrue(run.complete, run.steps)

    def test_all_three_workers_carry_the_one_seal(self):
        seals = {one["deployment"]["input_manifest"]["manifest_digest"]
                 for one in self.documents["stage_execution"]["workers"]}
        self.assertEqual(len(seals), 1)

    def test_the_job_names_that_seal_and_not_another(self):
        job = self.documents["submission"]["jobs"][0]
        self.assertEqual(job["input_digest"],
                         self.facts["manifest"]["manifest_digest"])

    def test_the_real_matches_check_accepts_every_stage(self):
        from tools.single_worker import _SingleWorker

        job = self.documents["submission"]["jobs"][0]
        for one in self.documents["stage_execution"]["workers"]:
            given = one["deployment"]
            stage = {"stage_id": f"{job['job_id']}/{one['role']}",
                     "kind": one["role"], "work_id": composer.WORK,
                     "profile_name": given["profile_name"],
                     "profile_digest": given["profile_digest"]}
            worker = _SingleWorker.__new__(_SingleWorker)
            worker.given = given
            # The real method, over the real documents. It raises on refusal.
            _SingleWorker._matches(worker, stage, job)

    def test_independence_is_carried_where_the_validator_looks_for_it(self):
        workers = self.documents["stage_execution"]["workers"]
        for member in ("participant", "principal", "launch_role",
                       "launch_home", "credential_home"):
            values = {one["deployment"][member] for one in workers}
            self.assertEqual(len(values), len(workers), member)


class TheSyntheticSourceIsLabelledAndPrivate(Composed):
    """R1. A stopgap for a deployment limitation, and nothing more."""

    def setUp(self):
        self.facts = composer.measured(run=no_engine)
        self.credential = self.facts["credential"]

    def test_the_marker_file_says_in_its_own_text_that_it_is_not_one(self):
        with open(self.credential["source"], encoding="utf-8") as handle:
            body = handle.read()
        self.assertIn("NOT-A-CREDENTIAL", body)
        self.assertIn("authorizes nothing", body)

    def test_both_documents_are_private_ordinary_files_this_user_owns(self):
        for place in (self.credential["source"], self.credential["registry"]):
            held = os.stat(place)
            self.assertTrue(stat.S_ISREG(held.st_mode))
            self.assertEqual(held.st_uid, os.geteuid())
            self.assertEqual(stat.S_IMODE(held.st_mode) & 0o077, 0)

    def test_the_registry_names_exactly_this_one_pair(self):
        from tools.user_credentials import held_registry

        with open(self.credential["registry"], encoding="utf-8") as handle:
            document = json.load(handle)
        sources = held_registry(document)
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["provider"], composer.FIXTURE_PROVIDER)
        self.assertEqual(sources[0]["reference"], composer.FIXTURE_REFERENCE)

    def test_the_real_resolver_reads_the_marker_back(self):
        """The whole point of the stopgap: the delivery this deployment cannot
        express as empty is expressed as one synthetic slot, and the canonical
        reader accepts it."""
        from baton_v12.worker_manager import credentials
        from tools.user_credentials import UserCredentialSources

        resolution = credentials.resolved_delivery(
            [composer.SLOT],
            profile={composer.SLOT: dict(self.credential["mapping"])})
        self.assertEqual(len(resolution), 1)
        reader = UserCredentialSources(self.credential["registry"],
                                       max_bearer=credentials.MAX_BEARER)
        bearer = reader.resolve(resolution[0]["provider"],
                                resolution[0]["reference"])
        self.assertIn("NOT-A-CREDENTIAL", bearer)

    def test_an_empty_delivery_is_still_refused_by_the_product(self):
        """The limitation is RECORDED, not worked around in the product. If
        this ever starts passing, the stopgap is what should be deleted."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.worker_manager import credentials

        with self.assertRaises(ContractRefusal):
            credentials.resolved_delivery([], profile={})


class NoPlaceholderSurvives(Composed):
    """R3. Every identity in the emitted documents is measured off something."""

    def setUp(self):
        run = composer.Run(composer.production_validators())
        self.facts, self.documents = composer.compose(
            run, facts=composer.measured(run=no_engine), write=False)

    def test_the_declared_base_is_the_targets_own_revision(self):
        base = self.facts["declared_base"]
        self.assertRegex(base, r"\A[0-9a-f]{40}\Z")
        self.assertNotEqual(base, "0" * 40)
        self.assertEqual(
            base, composer.declared_base(composer.DEST / "repo/target.git"))

    def test_a_target_with_no_main_ref_is_refused_rather_than_defaulted(self):
        import tempfile

        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(composer.Unmeasured):
                composer.declared_base(empty)

    def test_the_record_binding_digests_the_retained_snapshot_bytes(self):
        binding = self.facts["record_binding"]
        for name, member in (("FINDING.md", "finding_digest"),
                             ("PLAN.md", "plan_digest")):
            self.assertEqual(
                binding[member],
                composer.sha(composer.HERE / "record-snapshot" / name))

    def test_the_adapter_digest_measures_a_file_and_says_what_it_is_not(self):
        adapter = self.facts["adapter"]
        self.assertEqual(adapter["sha256"],
                         composer.sha(composer.REPO / adapter["path"]))
        self.assertIn("does_not_prove", adapter)

    def test_the_toolchain_measures_the_build_context_rather_than_the_image(self):
        toolchain = self.documents["toolchain"]
        self.assertGreater(toolchain["build_context_entries"], 1)
        self.assertNotEqual(toolchain["worker_source_manifest"],
                            composer.digest({"fixture": self.facts["image"]}))

    def test_an_absent_build_context_is_refused_rather_than_defaulted(self):
        import tempfile

        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaises(composer.Unmeasured):
                composer.build_context(os.path.join(empty, "nowhere"))
            with self.assertRaises(composer.Unmeasured):
                composer.build_context(empty)

    def test_the_policies_name_this_destination_and_no_earlier_one(self):
        rendered = json.dumps(self.documents["policies"])
        self.assertIn(str(composer.DEST), rendered)
        self.assertNotIn("baton-v12-lifecycle-198871", rendered)

    def test_the_task_is_the_accepted_contract_with_a_concrete_workload(self):
        task = self.documents["task"]
        self.assertEqual(task["schema"], "baton.dogfood-task/2")
        self.assertEqual(task["declared_base"], self.facts["declared_base"])
        self.assertIn("w197661-fixture.txt", task["instructions"])


if __name__ == "__main__":
    unittest.main()
