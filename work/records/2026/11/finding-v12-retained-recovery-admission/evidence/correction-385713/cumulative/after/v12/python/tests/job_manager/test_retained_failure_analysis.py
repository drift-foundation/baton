"""W385623 Stage 1-A — the retained verification failure, analysed and delivered.

WHAT THESE CASES ARE ABOUT. A terminal `verification-failed` ending whose
provider turn succeeded and whose retained candidate validates: the one
automatic analysis it earns, the exact evidence that analysis is fixed to, the
declared analysis authority that is permitted to author a report and nothing
else, and the one owner item the path delivers -- including the four finite
endings where no report ever arrives.

WHAT IS REAL HERE. The control store, its development line, its writer, its
attempts, its retained result manifests, its MEASURED candidate tree on
disk-backed storage and the composed typed failure cause are the accepted
operations (`tests.job_manager.test_review_driver`'s own `ReviewResultCase`,
whose purpose is exactly this: a reader of a frozen result is driven against
documents the manager really sealed). The Job store, its submission, its
stages, its cancellation fence and its operations journal are real. The
`result.json` the worker declared is a real file in real custody, read back
through the manager's own measurement.

WHAT IS FAKED, AND ONLY WHERE A DEPLOYMENT WOULD SUPPLY ONE: the checkpoint
profile and the authority-bound fence port the base case already supplies, and
the analysis worker DECLARATION -- which is configuration a deployment writes,
not behaviour. There is no provider, no model, no adapter, no image and no
container anywhere in this file; the "analysis" is a scripted document, which
is what the contract asks for -- "scripted diagnosis proves orchestration, not
live reasoning quality".

WHAT IS DELIBERATELY ABSENT. No owner decision, no successor admission, no
corrected verification, no review handoff and no receipt of any kind: those
are W385624's and W385625's, and a case here that produced one would be
implementing them. Nothing in this file writes a candidate, a verifier input
or an execution state -- and one case proves that by comparing the whole
control store's bytes across the entire path.
"""

import contextlib
import hashlib
import json
import os
import pathlib
import unittest

from baton_v12.contracts import ContractRefusal, digest, digest_of_bytes
from baton_v12.job_manager import (JobStore, cancellation, documents,
                                   ending, episodes, failure_analysis,
                                   fresh_attempt, job_control, manager,
                                   submission, submit, sweep)
from baton_v12.worker_manager import failure_cause, retain_manifest

from tests.job_manager import fixtures
from tests.job_manager import test_review_driver as driver
from tests.job_manager.fixtures import NOW, WORK_A, job, stage

WRITER = driver.WRITER
OWNER = "baton.slaw"
ANALYST = "baton.analysis"
ANALYST_PRINCIPAL = "principal:recovery-analysis"

# The owner-approved definition record this Work implements, by its canonical
# repository path. READ IN A CASE AND NOT IN THE PRODUCT: the module holds the
# definition as data and proves its own digest, and this file is what binds
# that held copy to the bytes the owner published. Declared in
# `tools/parallel_test.py` `CONSUMED_INPUTS`, which is what makes the run's
# source identity cover it.
APPROVED_PROFILE = (
    pathlib.Path(__file__).resolve().parents[4] / "work" / "records" / "2026"
    / "08" / "finding-v12-isolated-agent-workers" / "findings"
    / "finding-v12-team-hierarchy-shared-approvers" / "evidence"
    / "stage-1-contract-385615" / "stage1-analysis-1.json")
# The digest STAGE-1-CONTRACT.md section 5 pins for it.
APPROVED_PROFILE_DIGEST = (
    "a4be8b48e098efc47f770a8b7f941b80eadd22b23c48eebf67863d3a4dc824ab")

LATER = "2026-09-02T01:00:00.000Z"
# Past the approved 4800-second Job bound measured from the accepted
# admission, queue time included.
AFTER_DEADLINE = "2026-09-02T01:21:00.000Z"


def analysis_declaration(**changed):
    """One deployment's declared analysis authority.

    CONFIGURATION, NOT BEHAVIOUR, which is the whole point of the shape: the
    role is carried by a participant, a principal, a worker and an
    owner-approved profile. No adapter, image, model or provider is named --
    REC-8 forbids binding the role to one -- so a case that wanted to prove a
    provider was selected here would have nothing to assert against.
    """
    held = {"schema": failure_analysis.DECLARATION_SCHEMA,
            "role": failure_analysis.ANALYSIS_ROLE,
            "worker_id": "analysis-worker-1",
            "participant": ANALYST,
            "principal": ANALYST_PRINCIPAL,
            "profile": failure_analysis.ANALYSIS_PROFILE,
            "profile_digest": failure_analysis.ANALYSIS_PROFILE_DIGEST,
            "permitted_outputs": list(failure_analysis.PERMITTED_OUTPUTS),
            "capability_digest": "sha256:" + "c" * 64}
    held.update(changed)
    for name, value in list(held.items()):
        if value is ...:
            del held[name]
    return held


def analysis_report(key, input_digest, **changed):
    """One scripted diagnosis, in the bounded report contract."""
    held = {"schema": failure_analysis.REPORT_SCHEMA,
            "failure_key": key, "input_digest": input_digest,
            "facts": ["the required verification command exited 1",
                      "the command's third word carries an embedded newline"],
            "hypotheses": ["the newline was introduced when the argv was "
                           "composed for the task document"],
            "options": [{"option": "remove the embedded newline from the "
                                   "original argv",
                         "tradeoff": "verifies the same candidate under a "
                                     "command the owner must approve"},
                        {"option": "leave the command and reject the "
                                   "candidate",
                         "tradeoff": "discards a candidate whose own content "
                                     "was never examined"}],
            "recommendation": "remove the embedded newline and re-verify the "
                              "retained candidate only",
            "proposed_verification": {
                "argv": ["bash", "-c", "exec python3 -m unittest -v x"],
                "context_digest": "sha256:" + "e" * 64}}
    held.update(changed)
    return held


def worker_result(*, status=1, ending="verification-failed", provider=...,
                  verification=...):
    """The worker's own `result.json`, as a real document in real custody.

    `baton.dogfood-proposal/3` is one of the two generations
    `failure_cause.RETAINED_RESULT_SCHEMAS` reads. The members this suite
    cares about are the declared ending, the provider's account of itself and
    the verification's exit status; the rest is the record's own shape.
    """
    held = {"schema": "baton.dogfood-proposal/3",
            "task_id": "w385623-fixture-1",
            "disposition": ending,
            "why": f"the task's own command ended {status}",
            "changed_paths": ["v12/python/src/baton_v12/x.py"],
            "source_entries": 1, "collection": None,
            "base": driver.BASE, "entry_head": driver.BASE,
            "head": "f" * 40,
            "provider": ({"ok": True, "seconds_bound": 3600,
                          "seconds_bound_source": "job-selected"}
                         if provider is ... else provider),
            "verification": ({"status": status}
                             if verification is ... else verification),
            "context": None, "command": None, "exit_status": status,
            "candidate_changed": [], "candidate_removed": []}
    return json.dumps(held, indent=2, sort_keys=True).encode("utf-8")


class AnalysisCase(driver.ReviewResultCase):
    """One Job whose implementation attempt really ended verification-failed.

    The Job store is this suite's own, so the cancellation fence and the
    recovery journal are this case's. The control store, the line and the
    attempts are the base case's real ones.
    """

    def setUp(self):
        super().setUp()
        self.jobs.close()
        self.jobs = JobStore.open(
            os.path.join(self.root, "analysis-jobs.sqlite3"),
            authority_uuid=self.AUTHORITY, incarnation="jobs-analysis-1",
            clock=self.clock)
        self.addCleanup(self.jobs.close)
        submit(self.jobs, self.submission())
        self.custody = os.path.join(self.storage, "custody")
        os.mkdir(self.custody)
        self.declaration = analysis_declaration()

    # -- the two store fixtures ---------------------------------------------

    # WHICH FINITE CONTROL THIS CASE'S JOB IS ADMITTED UNDER. A class
    # attribute rather than a constant, because one production case needs a
    # Job that selects NONE: the Job's own stage deadline and the analysis's
    # admitted bound both run 4800 seconds from the same instant here, and a
    # case about the ANALYSIS bound alone cannot be driven while the Job's own
    # fence is reached first.
    CONTROL_PROFILE = job_control.NATIVE_HANDOFF_PROFILE

    def submission(self, profile=...):
        """One Job whose implementation and review stages name the same Work."""
        profile = self.CONTROL_PROFILE if profile is ... else profile
        held = job("job-a", stages=[
            stage("implementation", WORK_A),
            stage("review", WORK_A,
                  depends_on=[{"job_id": "job-a", "kind": "implementation"}])])
        if profile is None:
            return {"schema": documents.SUBMISSION_SCHEMA,
                    "submission_id": "sub-1", "jobs": [held]}
        held["control"] = {"profile": profile}
        return {"schema": documents.SUBMISSION_CONTROL_SCHEMA,
                "submission_id": "sub-1", "jobs": [held]}

    def reopened(self, incarnation="jobs-analysis-2"):
        """Another incarnation on the SAME Job store file.

        What a restart actually is here: a new handle over the durable rows,
        with no process cache and no live exchange to read.
        """
        store = JobStore.open(
            os.path.join(self.root, "analysis-jobs.sqlite3"),
            authority_uuid=self.AUTHORITY, incarnation=incarnation,
            clock=self.clock)
        self.addCleanup(store.close)
        return store

    # -- the manager rows and custody a real ending would have left ----------

    def _custody_tree(self, attempt_id, name, payload):
        """One measured output tree, really on disk, really digested."""
        place = os.path.join(self.custody, f"{attempt_id}--{name}")
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "result.json"), "wb") as handle:
            handle.write(payload)
        entries = [{"path": "result.json", "bytes": len(payload),
                    "content_digest": digest_of_bytes(payload)}]
        content = {"entries": entries, "entry_count": 1,
                   "total_bytes": len(payload),
                   "tree_digest": digest(entries)}
        return place, content

    def _output(self, attempt_id, name, *, kind, content, metadata,
                locator=None, content_digest=None, artifact_id=None):
        return {"name": name, "type": kind, "status": "present",
                "content_manifest": content,
                "artifact": {
                    "artifact_id": (artifact_id if artifact_id is not None
                                    else f"{attempt_id}:{name}"),
                    "media_type": "application/json",
                    "bytes": content["total_bytes"],
                    "content_digest": (content_digest if content_digest
                                       is not None
                                       else content["tree_digest"]),
                    "locator": locator},
                "result_metadata": metadata}

    def _frozen(self, attempt_id, *, disposition, outputs, result_id=None,
                participant=WRITER, generation=1):
        """Retain a result manifest and write the frozen rows beside it.

        THE ROWS AND THE MANIFEST ARE WRITTEN TO AGREE, because that agreement
        is one of the bindings under test: the artifact row, the manifest's
        artifact and the measured tree all name one candidate, and the cases
        that break one of them break exactly one.
        """
        result_id = result_id or ("result-" + attempt_id)
        self.control._connection.execute(
            "UPDATE attempts SET output = 'frozen', verification = 'failed' "
            "WHERE runtime_attempt_id = ?", (attempt_id,))
        document = dict(
            driver._result_vector(), result_id=result_id,
            disposition=disposition,
            assignment_ref={"work_ref": {"authority_uuid": self.AUTHORITY,
                                         "work_id": WORK_A},
                            "participant": participant,
                            "generation": generation},
            outputs=outputs)
        document.pop("manifest_digest")
        document["manifest_digest"] = digest(document)
        kept = retain_manifest(self.control, document,
                               "resultManifest")["digest"]
        self.control._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
            "manifest_digest, freeze_operation_id, frozen_at) VALUES "
            "(?, ?, ?, ?, ?, ?)",
            (attempt_id, result_id, disposition, kept,
             "freeze-" + attempt_id, NOW))
        for one in outputs:
            if one["status"] != "present" or one["artifact"] is None:
                continue
            self.control._connection.execute(
                "INSERT INTO output_artifacts (runtime_attempt_id, "
                "output_name, artifact_id, media_type, bytes, "
                "content_digest, locator) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (attempt_id, one["name"], one["artifact"]["artifact_id"],
                 one["artifact"]["media_type"], one["artifact"]["bytes"],
                 one["artifact"]["content_digest"],
                 one["artifact"]["locator"]))
        return kept, document

    def failed_attempt(self, number=1, *, status=1, ending=None,
                       provider=..., verification=..., payload=None,
                       claim=None, observation=None, disposition="unable",
                       artifact_id=None, content_digest=None,
                       participant=WRITER, result_id=None, locator=None,
                       outputs=None, attempt_id=None):
        """ONE terminal verification-failed ending, retained for real.

        The candidate output is the owned `git-change-proposal` type carrying
        the worker's own claim and its own ordinary-test observation; the tree
        beside it really holds the `result.json` whose digest this manager
        measured, which is what `failure_cause` opens to compose the typed
        declaration.
        """
        # `attempt_id` IS AN OPERAND SO A CASE CAN USE THE EPISODE'S OWN. The
        # production path observes a SETTLED Job-store ending, and that
        # ending's selectors are the episode's derived identities -- so a case
        # driving the real pass must retain its control-store attempt under
        # the identity the Job store already holds, not under a name of its
        # own. The default is unchanged for every existing case.
        attempt_id = (attempt_id if attempt_id is not None
                      else f"writer-attempt-{number}")
        self.attempt(attempt_id, number, participant,
                     f"writer-principal-{number}")
        self.completed(attempt_id)
        raw = payload if payload is not None else worker_result(
            status=status,
            ending=ending if ending is not None else "verification-failed",
            provider=provider, verification=verification)
        place, content = self._custody_tree(attempt_id, "proposal", raw)
        head = json.loads(raw)["head"] if payload is None else "f" * 40
        metadata = {
            failure_analysis.CANDIDATE_CLAIM: (
                claim if claim is not None else
                {"base": driver.BASE, "head": head,
                 "transport": "bundle/candidate.bundle",
                 "recap": "the candidate changed the source and its own "
                          "verification failed"}),
            failure_analysis.ORDINARY_TESTS: (
                observation if observation is not None else
                {"argv": ["bash", "-c", "exec python3 -m unittest -v x\n"],
                 "base": driver.BASE, "head": head, "status": status,
                 "task_digest": "sha256:" + "7" * 64,
                 "task_id": "w385623-fixture-1"})}
        held = outputs if outputs is not None else [
            self._output(attempt_id, "proposal", kind="git-change-proposal",
                         content=content, metadata=metadata,
                         locator=(locator if locator is not None
                                  else "file://" + place),
                         artifact_id=artifact_id,
                         content_digest=content_digest)]
        kept, document = self._frozen(attempt_id, disposition=disposition,
                                      outputs=held, result_id=result_id,
                                      participant=participant,
                                      generation=number)
        return {"attempt_id": attempt_id, "manifest": kept,
                "document": document, "custody": place, "content": content,
                "result_id": document["result_id"], "payload": raw}

    def analysis_outputs(self, attempt_id, *, report, partial=True):
        """The permitted outputs one analysis really wrote, measured on disk.

        EXTRACTED SO THE PRODUCTION PATH CAN FREEZE IN TWO STEPS. A replay
        analysis worker driven by the manager's own pass is admitted and
        started on one tick and freezes its result on a later one, which is
        what an in-flight analysis IS; a helper that could only do both at
        once could not express it.
        """
        body = json.dumps(report, indent=2, sort_keys=True).encode("utf-8")
        place, content = self._custody_tree(attempt_id, "analysis", body)
        held = [self._output(
            attempt_id, failure_analysis.ANALYSIS_OUTPUT,
            kind="record-output", content=content,
            metadata={failure_analysis.REPORT_SCHEMA: report},
            locator="file://" + place)]
        if partial:
            scratch, measured = self._custody_tree(
                attempt_id, "partial", b"{\"read\": 3}\n")
            held.append(self._output(
                attempt_id, failure_analysis.PARTIAL_OUTPUT,
                kind="directory-result", content=measured, metadata={},
                locator="file://" + scratch))
        return held

    def analysed_attempt(self, number=1, *, report=None, outputs=None,
                         participant=ANALYST, partial=True,
                         disposition="completed", attempt_id=None):
        """The declared analyst's own invocation and its frozen report.

        The analysis writes exactly its permitted outputs. It materializes no
        candidate and names no base or head: a diagnosis is about evidence,
        and this fixture cannot express an analysis that proposes one without
        being changed to break that rule on purpose -- which one case does.
        """
        # AND THE ANALYSIS ATTEMPT IDENTITY IS AN OPERAND FOR THE SAME REASON
        # the failed attempt's is: the production pass DERIVES it from the
        # failure key, so a replay analysis worker driven by that pass must
        # retain its result under the identity the dispatch intent named.
        attempt_id = (attempt_id if attempt_id is not None
                      else f"analysis-attempt-{number}")
        self.attempt(attempt_id, number, participant,
                     f"analysis-principal-{number}")
        self.completed(attempt_id)
        held = (self.analysis_outputs(attempt_id, report=report,
                                      partial=partial)
                if outputs is None else outputs)
        self._frozen(attempt_id, disposition=disposition, outputs=held,
                     participant=participant, generation=number)
        return attempt_id

    # -- the acts under test -------------------------------------------------

    def observed(self, failed=None, *, declaration=None, episode=1,
                 stage_id="job-a/implementation", now=None, store=None):
        held = failed if failed is not None else self.failed_attempt()
        return failure_analysis.observe_terminal_failure(
            store if store is not None else self.jobs, self.control,
            stage_id=stage_id, episode=episode,
            attempt_id=held["attempt_id"],
            declaration=(declaration if declaration is not None
                         else self.declaration),
            now=now if now is not None else NOW)

    def whole_path(self, *, number=1, report=None, store=None):
        """Observe, dispatch, analyse and deliver -- the ordinary outcome."""
        store = store if store is not None else self.jobs
        failed = self.failed_attempt(number)
        seen = self.observed(failed, store=store)
        key = seen["failure"]["failure_key"]
        document = report if report is not None else analysis_report(
            key, seen["intent"]["input_digest"])
        analysis = self.analysed_attempt(number, report=document)
        failure_analysis.admit_dispatch(store, self.control, key=key,
                                        analysis_attempt_id=analysis, now=NOW)
        delivered = failure_analysis.deliver_analysis(
            store, self.control, key=key, destination=OWNER, now=LATER)
        return {"failed": failed, "observed": seen, "key": key,
                "analysis_attempt_id": analysis, "report": document,
                "delivered": delivered}

    def repointed(self, failed, **changed):
        """Retain ANOTHER result manifest for the same attempt and point the
        frozen row at it, leaving every artifact binding intact."""
        document = dict(failed["document"])
        held = [dict(one) for one in document["outputs"]]
        claim = dict(held[0]["result_metadata"][
            failure_analysis.CANDIDATE_CLAIM])
        claim.update(changed)
        held[0]["result_metadata"] = dict(
            held[0]["result_metadata"],
            **{failure_analysis.CANDIDATE_CLAIM: claim})
        document["outputs"] = held
        document.pop("manifest_digest")
        document["manifest_digest"] = digest(document)
        kept = retain_manifest(self.control, document,
                               "resultManifest")["digest"]
        self.control._connection.execute(
            "UPDATE outputs SET manifest_digest = ? WHERE "
            "runtime_attempt_id = ?", (kept, failed["attempt_id"]))
        return kept

    def refusal(self, call, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            call(*operands, **named)
        return caught.exception

    def journal(self, kind, store=None):
        store = store if store is not None else self.jobs
        return [row["operation_id"] for row in store._connection.execute(
            "SELECT operation_id FROM operations WHERE kind = ? ORDER BY "
            "operation_id", (kind,))]

    def cancel(self, job_id="job-a", reason="the owner stopped it"):
        return cancellation.request(self.jobs, job_id=job_id, reason=reason)


# -- 1. the ordinary outcome -------------------------------------------------


class AValidRetainedFailureEarnsOneAnalysisAndOneOwnerItem(AnalysisCase):
    """The first usable result of 1-A, end to end and automatic."""

    def test_the_whole_path_records_five_facts_and_delivers_one_item(self):
        held = self.whole_path()
        store, key = self.jobs, held["key"]
        self.assertIsNotNone(failure_analysis.failure_of(store, key))
        self.assertIsNotNone(failure_analysis.intent_of(store, key))
        self.assertIsNotNone(failure_analysis.dispatch_of(store, key))
        self.assertIsNotNone(failure_analysis.report_of(store, key))
        item = failure_analysis.owner_item_of(store, key)
        self.assertEqual(item["outcome"], "reported")
        self.assertEqual(item["destination"], OWNER)
        self.assertEqual(item["delivered_at"], LATER)
        self.assertIsNone(item["why"])
        self.assertEqual(failure_analysis.recovery_disposition(store, key),
                         "delivered")
        # EXACTLY ONE OF EACH, counted in the journal rather than inferred.
        for kind in (failure_analysis.FAILURE_KIND,
                     failure_analysis.INTENT_KIND,
                     failure_analysis.DISPATCH_KIND,
                     failure_analysis.REPORT_KIND,
                     failure_analysis.OWNER_ITEM_KIND):
            self.assertEqual(len(self.journal(kind)), 1, kind)

    def test_the_failure_key_is_the_six_selectors_the_contract_names(self):
        held = self.whole_path()
        record = failure_analysis.failure_of(self.jobs, held["key"])
        self.assertEqual(
            held["key"],
            failure_analysis.failure_key(
                authority_uuid=self.AUTHORITY, work_id=WORK_A,
                job_id="job-a", stage_id="job-a/implementation",
                attempt_id=held["failed"]["attempt_id"],
                result_id=held["failed"]["result_id"]))
        self.assertEqual(
            {name: record["selectors"][name]
             for name in failure_analysis.FAILURE_SELECTORS},
            {"authority_uuid": self.AUTHORITY, "work_id": WORK_A,
             "job_id": "job-a", "stage_id": "job-a/implementation",
             "attempt_id": held["failed"]["attempt_id"],
             "result_id": held["failed"]["result_id"]})

    def test_the_record_binds_the_candidate_to_bytes_and_not_to_a_name(self):
        held = self.whole_path()
        record = failure_analysis.failure_of(self.jobs, held["key"])
        candidate = record["candidate"]
        measured = held["failed"]["content"]
        self.assertEqual(candidate["base"], driver.BASE)
        self.assertEqual(candidate["head"],
                         json.loads(held["failed"]["payload"])["head"])
        self.assertEqual(candidate["tree_digest"], measured["tree_digest"])
        self.assertEqual(candidate["content_digest"], measured["tree_digest"])
        self.assertEqual(candidate["entry_count"], 1)
        self.assertEqual(candidate["artifact_id"],
                         f"{held['failed']['attempt_id']}:proposal")
        self.assertEqual(candidate["locator"],
                         "file://" + held["failed"]["custody"])

    def test_the_record_binds_the_original_argv_task_and_exit_status(self):
        held = self.whole_path()
        record = failure_analysis.failure_of(self.jobs, held["key"])
        self.assertEqual(record["verification"],
                         {"attempted": True, "status": 1,
                          "argv": ["bash", "-c",
                                   "exec python3 -m unittest -v x\n"],
                          "task_id": "w385623-fixture-1",
                          "task_digest": "sha256:" + "7" * 64})
        # THE EMBEDDED NEWLINE SURVIVES VERBATIM, which is the fixture's
        # point: the original command is immutable evidence, and a record that
        # normalized it would hide the exact defect an owner must approve a
        # correction for.
        self.assertIn("\n", record["verification"]["argv"][2])

    def test_the_intent_pins_the_declared_authority_and_approved_bounds(self):
        held = self.whole_path()
        intent = failure_analysis.intent_of(self.jobs, held["key"])
        self.assertEqual(intent["role"], "analysis")
        self.assertEqual(intent["participant"], ANALYST)
        self.assertEqual(intent["principal"], ANALYST_PRINCIPAL)
        self.assertEqual(intent["worker_id"], "analysis-worker-1")
        self.assertEqual(intent["profile"], "stage1-analysis/1")
        self.assertEqual(intent["profile_digest"],
                         "sha256:" + APPROVED_PROFILE_DIGEST)
        self.assertEqual(
            intent["declaration_digest"],
            failure_analysis.declaration_digest(self.declaration))
        self.assertEqual(intent["policy"]["automatic_retries"], 0)
        self.assertEqual(intent["policy"]["automatic_corrections"], 0)
        self.assertEqual(intent["deadlines"],
                         {"admitted_at": NOW,
                          "job_deadline_at": "2026-09-02T01:20:00.000Z",
                          "job_seconds": 4800, "includes_queue": True,
                          "stage_seconds": 4800,
                          "stage_origin": "stage_admission",
                          "provider_invocation_seconds": 3600,
                          "provider_invocation_origin": "invocation_start"})

    def test_the_owner_item_resolves_the_exact_report_the_analyst_wrote(self):
        held = self.whole_path()
        item = failure_analysis.owner_item_of(self.jobs, held["key"])
        record = failure_analysis.report_of(self.jobs, held["key"])
        self.assertEqual(item["report_digest"], record["report_digest"])
        self.assertEqual(record["report_digest"],
                         failure_analysis.report_digest(held["report"]))
        self.assertEqual(record["analysis_attempt_id"],
                         held["analysis_attempt_id"])
        self.assertEqual(record["outputs"], ["analysis", "partial"])
        self.assertEqual(record["ending"], "completed")
        self.assertEqual(item["input_digest"], record["input_digest"])

    def test_the_delivered_report_separates_facts_from_hypotheses(self):
        held = self.whole_path()
        document = held["delivered"]["report_document"]
        self.assertEqual(document["schema"], failure_analysis.REPORT_SCHEMA)
        self.assertTrue(document["facts"])
        self.assertTrue(document["hypotheses"])
        self.assertEqual(len(document["options"]), 2)
        self.assertTrue(document["recommendation"])
        # A PROPOSAL AND NOT AN ADMISSION. The corrected command travels and
        # nothing here consumes it: no successor, no verification, no receipt.
        self.assertEqual(document["proposed_verification"]["argv"][0], "bash")
        self.assertNotIn("\n", document["proposed_verification"]["argv"][2])
        # AND NOTHING ADMITTED A SUCCESSOR OR OPENED A CORRECTION ROUND.
        # W385624 owns the owner decision and the successor admission; a
        # journal row of either kind here would be this slice implementing it.
        for kind in (fresh_attempt.INTENT_KIND, fresh_attempt.ADMIT_KIND,
                     episodes.CORRECT_KIND, job_control.EXPIRY_KIND,
                     cancellation.REQUEST_KIND):
            self.assertEqual(self.journal(kind), [], kind)

    def test_the_partial_material_the_analysis_wrote_is_preserved(self):
        held = self.whole_path()
        item = failure_analysis.owner_item_of(self.jobs, held["key"])
        self.assertEqual([one["name"] for one in item["partials"]],
                         ["analysis", "partial"])
        for one in item["partials"]:
            self.assertTrue(one["content_digest"].startswith("sha256:"))
            self.assertGreater(one["bytes"], 0)

    def test_the_disposition_advances_through_its_closed_vocabulary(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        self.assertEqual(failure_analysis.recovery_disposition(self.jobs, key),
                         "analysis-intended")
        report = analysis_report(key, seen["intent"]["input_digest"])
        analysis = self.analysed_attempt(1, report=report)
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=analysis, now=NOW)
        self.assertEqual(failure_analysis.recovery_disposition(self.jobs, key),
                         "analysis-dispatched")
        failure_analysis.deliver_analysis(self.jobs, self.control, key=key,
                                          destination=OWNER, now=LATER)
        self.assertEqual(failure_analysis.recovery_disposition(self.jobs, key),
                         "delivered")
        self.assertIsNone(
            failure_analysis.recovery_disposition(self.jobs, "sha256:" + "0" * 64))

    def test_the_fixed_input_is_what_the_intent_and_the_report_agree_on(self):
        held = self.whole_path()
        failure = failure_analysis.failure_of(self.jobs, held["key"])
        intent = failure_analysis.intent_of(self.jobs, held["key"])
        self.assertEqual(failure["input_digest"], intent["input_digest"])
        self.assertEqual(held["report"]["input_digest"],
                         intent["input_digest"])
        # AND IT IS DERIVABLE AGAIN FROM THE SAME EVIDENCE, which is what
        # makes it a fact about the ending rather than a value this run chose.
        current = failure_analysis.classified_failure(
            self.control, held["failed"]["attempt_id"])
        again = failure_analysis.analysis_input(
            current, failure_key=held["key"], job_id="job-a",
            stage_id="job-a/implementation", episode=1)
        self.assertEqual(failure_analysis.input_digest(again),
                         failure["input_digest"])
        self.assertEqual(again["schema"], failure_analysis.INPUT_SCHEMA)


# -- 2. the trigger, and everything that is not it ---------------------------


class TheTriggerIsRefusedExplicitlyAndNeverSilentlyUsed(AnalysisCase):
    """Invalid candidate or evidence is REPORTED. The contract forbids
    treating any of these as eligible recovery input."""

    def classify(self, failed):
        return failure_analysis.classified_failure(self.control,
                                                   failed["attempt_id"])

    def test_an_attempt_that_froze_nothing_is_refused(self):
        self.attempt("writer-attempt-9", 9, WRITER, "writer-principal-9")
        self.completed("writer-attempt-9")
        failure = self.refusal(failure_analysis.classified_failure,
                              self.control, "writer-attempt-9")
        self.assertIn("froze no result", str(failure))

    def test_a_completed_candidate_ending_is_not_reclassified(self):
        failed = self.failed_attempt(disposition="completed")
        self.assertIn("is not reclassified here",
                      str(self.refusal(self.classify, failed)))

    def test_an_absent_retained_manifest_is_reported_not_assumed(self):
        failed = self.failed_attempt()
        self.control._connection.execute(
            "UPDATE outputs SET manifest_digest = ? WHERE "
            "runtime_attempt_id = ?",
            ("sha256:" + "4" * 64, failed["attempt_id"]))
        self.assertIn("never treated as eligible recovery input",
                      str(self.refusal(self.classify, failed)))

    def test_a_result_with_no_candidate_output_is_not_recovery_input(self):
        failed = self.failed_attempt(outputs=[])
        self.assertIn("is not recovery input",
                      str(self.refusal(self.classify, failed)))

    def test_a_candidate_whose_artifact_is_another_attempts_is_refused(self):
        failed = self.failed_attempt(artifact_id="writer-attempt-2:proposal")
        self.assertIn("is not the one this attempt's own seal composed",
                      str(self.refusal(self.classify, failed)))

    def test_a_candidate_whose_digest_is_not_the_measured_tree_is_refused(self):
        failed = self.failed_attempt(content_digest="sha256:" + "5" * 64)
        held = self.refusal(self.classify, failed)
        self.assertEqual(held.code, "digest")

    def test_an_artifact_row_disagreeing_with_the_manifest_is_refused(self):
        failed = self.failed_attempt()
        self.control._connection.execute(
            "UPDATE output_artifacts SET locator = 'file:///elsewhere' "
            "WHERE runtime_attempt_id = ?", (failed["attempt_id"],))
        self.assertIn("disagree about the frozen candidate",
                      str(self.refusal(self.classify, failed)))

    def test_a_claim_and_its_own_observation_must_agree_on_the_candidate(self):
        failed = self.failed_attempt(
            observation={"argv": ["true"], "base": driver.BASE,
                         "head": "0" * 40, "status": 1,
                         "task_digest": "sha256:" + "7" * 64,
                         "task_id": "w385623-fixture-1"})
        held = self.refusal(self.classify, failed)
        self.assertEqual(held.category, "ambiguous")
        self.assertIn("not resolved by picking a half", str(held))

    def test_a_candidate_carrying_no_ordinary_test_observation_is_refused(self):
        attempt_id = "writer-attempt-7"
        self.attempt(attempt_id, 7, WRITER, "writer-principal-7")
        self.completed(attempt_id)
        place, content = self._custody_tree(attempt_id, "proposal",
                                           worker_result())
        self._frozen(attempt_id, disposition="unable", outputs=[
            self._output(attempt_id, "proposal", kind="git-change-proposal",
                         content=content, locator="file://" + place,
                         metadata={failure_analysis.CANDIDATE_CLAIM: {
                             "base": driver.BASE, "head": "f" * 40,
                             "transport": "bundle/x", "recap": "x"}})],
                     generation=7)
        self.assertIn("will not invent either",
                      str(self.refusal(failure_analysis.classified_failure,
                                       self.control, attempt_id)))

    def test_a_passed_verification_is_not_this_trigger(self):
        failed = self.failed_attempt(status=0, ending="candidate")
        self.assertIn("declared 'candidate' and this trigger is "
                      "'verification-failed'",
                      str(self.refusal(self.classify, failed)))

    def test_a_verification_status_zero_declared_unable_is_still_refused(self):
        failed = self.failed_attempt(status=0)
        self.assertIn("declares verification status 0",
                      str(self.refusal(self.classify, failed)))

    def test_an_unrun_verification_is_the_absence_of_evidence(self):
        failed = self.failed_attempt(verification=None)
        self.assertIn("is the absence of evidence",
                      str(self.refusal(self.classify, failed)))

    def test_a_provider_failure_is_a_different_ending(self):
        failed = self.failed_attempt(
            ending="provider-failed",
            provider={"ok": False, "failure_reason": "timeout",
                      "seconds_bound": 3600,
                      "seconds_bound_source": "job-selected"})
        self.assertIn("general exceptional-ending classification",
                      str(self.refusal(self.classify, failed)))

    def test_a_verification_failed_ending_naming_a_provider_reason_refuses(self):
        failed = self.failed_attempt(
            provider={"ok": True, "failure_reason": "api-error",
                      "seconds_bound": 3600,
                      "seconds_bound_source": "job-selected"})
        self.assertIn("requires a SUCCESSFUL provider turn",
                      str(self.refusal(self.classify, failed)))

    def test_two_accounts_of_the_exit_status_are_refused_as_ambiguous(self):
        failed = self.failed_attempt(
            payload=worker_result(status=2),
            observation={"argv": ["true"], "base": driver.BASE,
                         "head": "f" * 40, "status": 1,
                         "task_digest": "sha256:" + "7" * 64,
                         "task_id": "w385623-fixture-1"})
        held = self.refusal(self.classify, failed)
        self.assertEqual(held.category, "ambiguous")
        self.assertIn("one account of its command", str(held))

    def test_a_substituted_result_json_fails_its_own_measurement(self):
        """The measured bytes are the binding, and this is what breaks it."""
        failed = self.failed_attempt()
        self.classify(failed)
        with open(os.path.join(failed["custody"], "result.json"), "wb") as f:
            f.write(worker_result(status=9))
        self.assertIn("declared no owned ending",
                      str(self.refusal(self.classify, failed)))
        # AND THE OWNER OF THE MEASUREMENT SAYS WHY, in as many words: the
        # substituted file does not recompute to the digest the seal measured.
        declaration = failure_cause.declaration_of(
            failure_cause.attempt_failure_cause_of(self.control,
                                                   failed["attempt_id"]))
        known, _value = failure_cause.decode(declaration["declared_ending"])
        self.assertFalse(known)
        self.assertIn("does not recompute",
                      declaration["declared_ending"]["why"])

    def test_a_result_json_in_a_generation_this_build_cannot_read_refuses(self):
        failed = self.failed_attempt(
            payload=json.dumps({"schema": "baton.dogfood-proposal/9",
                                "disposition": "verification-failed"},
                               sort_keys=True).encode("utf-8"))
        self.assertIn("declared no owned ending",
                      str(self.refusal(self.classify, failed)))

    def test_nothing_is_journalled_by_a_refused_observation(self):
        failed = self.failed_attempt(status=0)
        self.refusal(self.observed, failed)
        self.assertEqual(self.journal(failure_analysis.FAILURE_KIND), [])
        self.assertEqual(self.journal(failure_analysis.INTENT_KIND), [])


# -- 3. the declared analysis authority --------------------------------------


class TheAnalysisRoleIsDeclaredConfigurationAndNotAProvider(AnalysisCase):
    """REC-8: the role is bound through declared worker/profile configuration,
    without binding it to a provider or model."""

    def denied(self, **changed):
        return self.refusal(failure_analysis.check_analysis_declaration,
                            analysis_declaration(**changed))

    def test_the_default_declaration_is_admitted_and_names_no_provider(self):
        held = failure_analysis.check_analysis_declaration(self.declaration)
        self.assertEqual(held["role"], "analysis")
        text = json.dumps(held).lower()
        for word in ("claude", "opus", "anthropic", "codex", "model",
                     "image", "adapter"):
            self.assertNotIn(word, text)

    def test_a_missing_or_extra_member_is_refused(self):
        self.assertIn("missing participant", str(self.denied(participant=...)))
        self.assertIn("unexpected model",
                      str(self.denied(model="some-model")))

    def test_another_schema_revision_is_refused_rather_than_part_read(self):
        held = self.denied(schema="baton.v12.recovery-analysis-worker/2")
        self.assertEqual(held.category, "policy")

    def test_an_implementation_lane_does_not_carry_the_analysis_role(self):
        held = self.denied(role="implementation")
        self.assertIn("does not carry it", str(held))
        self.assertIn("review", str(self.denied(role="review")))

    def test_an_unapproved_profile_selection_is_refused(self):
        self.assertIn("is the owner's and is not inferred",
                      str(self.denied(profile="stage1-analysis/2")))

    def test_a_profile_digest_that_is_not_the_published_one_is_refused(self):
        held = self.denied(profile_digest="sha256:" + "0" * 64)
        self.assertEqual(held.code, "digest")
        self.assertIn("exact agreement", str(held))

    def test_a_widened_permitted_output_set_is_refused(self):
        self.assertIn("may not author",
                      str(self.denied(permitted_outputs=[
                          "analysis", "partial", "proposal"])))
        self.assertIn("may not author",
                      str(self.denied(permitted_outputs=["analysis"])))

    def test_one_value_cannot_be_both_participant_and_principal(self):
        self.assertIn("cannot attribute either",
                      str(self.denied(principal=ANALYST)))

    def test_an_unusable_declaration_refuses_before_anything_is_recorded(self):
        failed = self.failed_attempt()
        self.refusal(self.observed, failed,
                     declaration=analysis_declaration(role="implementation"))
        self.assertEqual(self.journal(failure_analysis.FAILURE_KIND), [])
        self.assertEqual(self.journal(failure_analysis.INTENT_KIND), [])

    def test_the_declaration_digest_is_over_the_whole_document(self):
        one = failure_analysis.declaration_digest(analysis_declaration())
        two = failure_analysis.declaration_digest(
            analysis_declaration(worker_id="analysis-worker-2"))
        self.assertNotEqual(one, two)


# -- 4. wrong binding -------------------------------------------------------


class TheWrongBindingIsRefusedBeforeAnythingIsWritten(AnalysisCase):

    def test_a_stage_of_another_job_cannot_carry_this_failure(self):
        failed = self.failed_attempt()
        self.assertIn("carries no stage",
                      str(self.refusal(self.observed, failed,
                                       stage_id="job-b/implementation")))

    def test_a_stage_naming_another_work_refuses_the_attribution(self):
        failed = self.failed_attempt()
        self.jobs._connection.execute(
            "UPDATE stages SET work_id = ? WHERE stage_id = ?",
            ("0000000a-W9", "job-a/implementation"))
        self.assertIn("attributed to the Work that was executing",
                      str(self.refusal(self.observed, failed)))

    def test_another_authoritys_store_refuses_the_record(self):
        failed = self.failed_attempt()
        foreign = JobStore.open(
            os.path.join(self.root, "foreign-jobs.sqlite3"),
            authority_uuid="0000000b" + "0" * 24,
            incarnation="jobs-foreign", clock=self.clock)
        self.addCleanup(foreign.close)
        submit(foreign, self.submission())
        self.assertIn("one store's records are one Authority's",
                      str(self.refusal(self.observed, failed, store=foreign)))

    def test_a_report_about_another_failure_is_not_evidence_about_this_one(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        analysis = self.analysed_attempt(
            1, report=analysis_report("sha256:" + "1" * 64,
                                      seen["intent"]["input_digest"]))
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=analysis, now=NOW)
        self.assertIn("another failure is not evidence about this one",
                      str(self.refusal(failure_analysis.deliver_analysis,
                                       self.jobs, self.control, key=key,
                                       destination=OWNER, now=LATER)))

    def test_a_report_about_another_input_digest_is_refused(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        analysis = self.analysed_attempt(
            1, report=analysis_report(key, "sha256:" + "2" * 64))
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=analysis, now=NOW)
        held = self.refusal(failure_analysis.deliver_analysis, self.jobs,
                            self.control, key=key, destination=OWNER,
                            now=LATER)
        self.assertEqual(held.code, "digest")
        self.assertIn("the fixed evidence its intent named", str(held))

    def test_an_analysis_executed_by_another_participant_is_refused(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        analysis = self.analysed_attempt(
            1, report=analysis_report(key, seen["intent"]["input_digest"]),
            participant=WRITER)
        self.assertIn("does not adopt another participant's execution",
                      str(self.refusal(failure_analysis.admit_dispatch,
                                       self.jobs, self.control, key=key,
                                       analysis_attempt_id=analysis,
                                       now=NOW)))

    def test_an_analysis_that_authored_a_candidate_is_refused_as_one(self):
        """The role may inspect evidence and author its report ONLY."""
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        report = analysis_report(key, seen["intent"]["input_digest"])
        attempt_id = "analysis-attempt-1"
        self.attempt(attempt_id, 1, ANALYST, "analysis-principal-1")
        self.completed(attempt_id)
        place, content = self._custody_tree(
            attempt_id, "analysis",
            json.dumps(report, indent=2, sort_keys=True).encode("utf-8"))
        candidate, measured = self._custody_tree(attempt_id, "proposal",
                                                 worker_result())
        self._frozen(attempt_id, disposition="completed", outputs=[
            self._output(attempt_id, failure_analysis.ANALYSIS_OUTPUT,
                         kind="record-output", content=content,
                         metadata={failure_analysis.REPORT_SCHEMA: report},
                         locator="file://" + place),
            self._output(attempt_id, "proposal", kind="git-change-proposal",
                         content=measured, metadata={},
                         locator="file://" + candidate)],
                     participant=ANALYST)
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=attempt_id,
                                        now=NOW)
        held = self.refusal(failure_analysis.deliver_analysis, self.jobs,
                            self.control, key=key, destination=OWNER,
                            now=LATER)
        self.assertEqual(held.category, "policy")
        self.assertIn("may not author a candidate", str(held))
        self.assertIsNone(failure_analysis.report_of(self.jobs, key))
        self.assertIsNone(failure_analysis.owner_item_of(self.jobs, key))

    def test_an_analysis_result_carrying_no_report_is_refused(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        attempt_id = "analysis-attempt-1"
        self.attempt(attempt_id, 1, ANALYST, "analysis-principal-1")
        self.completed(attempt_id)
        place, content = self._custody_tree(attempt_id, "analysis", b"{}\n")
        self._frozen(attempt_id, disposition="completed", outputs=[
            self._output(attempt_id, failure_analysis.ANALYSIS_OUTPUT,
                         kind="record-output", content=content, metadata={},
                         locator="file://" + place)],
                     participant=ANALYST)
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=attempt_id,
                                        now=NOW)
        self.assertIn("will not invent one",
                      str(self.refusal(failure_analysis.deliver_analysis,
                                       self.jobs, self.control, key=key,
                                       destination=OWNER, now=LATER)))

    def test_a_malformed_report_is_refused_member_by_member(self):
        key = "sha256:" + "3" * 64
        base = analysis_report(key, "sha256:" + "4" * 64)
        for changed, expected in (
                ({"facts": []}, "non-empty"),
                ({"facts": "a sentence"}, "is a list"),
                ({"options": []}, "non-empty"),
                ({"options": [{"option": "x"}]}, "tradeoff"),
                ({"recommendation": ""}, "durable text"),
                ({"schema": "baton.v12.recovery-analysis-report/2"},
                 "reads exactly"),
                ({"proposed_verification": {"argv": "cmd",
                                            "context_digest": "sha256:x"}},
                 "assemble from a string is a shell")):
            held = dict(base, **changed)
            self.assertIn(expected,
                          str(self.refusal(
                              failure_analysis.check_analysis_report, held)),
                          changed)
        # AN EMPTY HYPOTHESIS LIST IS ADMITTED: a diagnosis that needed to
        # guess nothing is a diagnosis.
        failure_analysis.check_analysis_report(dict(base, hypotheses=[]))


# -- 5. duplicates and concurrent observation --------------------------------


class OneEndingIsOneAnalysisHoweverOftenItIsObserved(AnalysisCase):
    """"Repeated publication/notification of the same ending does not create
    another analysis or owner item.\""""

    def test_a_second_observation_replays_and_writes_nothing(self):
        failed = self.failed_attempt()
        first = self.observed(failed)
        second = self.observed(failed, now=LATER)
        self.assertEqual(first["failure"], second["failure"])
        self.assertEqual(first["intent"], second["intent"])
        # THE DEADLINE IS THE FIRST ADMISSION'S, not the second observer's.
        self.assertEqual(second["intent"]["deadlines"]["admitted_at"], NOW)
        self.assertEqual(len(self.journal(failure_analysis.FAILURE_KIND)), 1)
        self.assertEqual(len(self.journal(failure_analysis.INTENT_KIND)), 1)

    def test_two_concurrent_observers_produce_one_intent(self):
        failed = self.failed_attempt()
        other = self.reopened("jobs-analysis-concurrent")
        one = self.observed(failed)
        two = self.observed(failed, store=other, now=LATER)
        self.assertEqual(one["intent"], two["intent"])
        self.assertEqual(len(self.journal(failure_analysis.INTENT_KIND)), 1)
        self.assertEqual(
            len(self.journal(failure_analysis.INTENT_KIND, store=other)), 1)

    def test_a_renewed_failure_has_its_own_distinct_key(self):
        one = self.observed(self.failed_attempt(1))
        two = self.observed(self.failed_attempt(2), episode=2)
        self.assertNotEqual(one["failure"]["failure_key"],
                            two["failure"]["failure_key"])
        self.assertEqual(len(self.journal(failure_analysis.FAILURE_KIND)), 2)
        self.assertEqual(len(self.journal(failure_analysis.INTENT_KIND)), 2)
        self.assertEqual(sorted(failure_analysis.failures_of(self.jobs)),
                         sorted([one["failure"]["failure_key"],
                                 two["failure"]["failure_key"]]))

    def test_the_same_ending_filed_under_changed_operands_collides(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        held = self.refusal(
            failure_analysis.record_failure, self.jobs,
            classified=failure_analysis.classified_failure(
                self.control, failed["attempt_id"]),
            job_id="job-a", stage_id="job-a/implementation", episode=9)
        self.assertEqual(held.code, "operation-collision")
        self.assertEqual(
            failure_analysis.failure_of(self.jobs,
                                        seen["failure"]["failure_key"]),
            seen["failure"])

    def test_a_second_delivery_of_the_same_item_replays(self):
        held = self.whole_path()
        again = failure_analysis.deliver_analysis(
            self.jobs, self.control, key=held["key"], destination=OWNER,
            now="2026-09-02T02:00:00.000Z")
        self.assertEqual(again["owner_item"],
                         held["delivered"]["owner_item"])
        self.assertEqual(
            len(self.journal(failure_analysis.OWNER_ITEM_KIND)), 1)

    def test_a_dispatch_naming_a_second_execution_collides(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        one = self.analysed_attempt(
            1, report=analysis_report(key, seen["intent"]["input_digest"]))
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=one, now=NOW)
        two = self.analysed_attempt(
            2, report=analysis_report(key, seen["intent"]["input_digest"]))
        held = self.refusal(failure_analysis.admit_dispatch, self.jobs,
                            self.control, key=key, analysis_attempt_id=two,
                            now=NOW)
        self.assertEqual(held.code, "operation-collision")
        self.assertEqual(len(self.journal(failure_analysis.DISPATCH_KIND)), 1)

    def test_a_record_of_another_failure_copied_to_this_identity_refuses(self):
        """A signature is not ownership."""
        held = self.whole_path()
        other = self.observed(self.failed_attempt(2), episode=2)
        self.jobs._connection.execute(
            "UPDATE operations SET result = (SELECT result FROM operations "
            "WHERE operation_id = ?) WHERE operation_id = ?",
            (failure_analysis.failure_operation_id(
                other["failure"]["failure_key"]),
             failure_analysis.failure_operation_id(held["key"])))
        self.assertIn("proved to be this failure's",
                      str(self.refusal(failure_analysis.failure_of,
                                       self.jobs, held["key"])))


# -- 6. crash and restart at every cut ---------------------------------------


class TheAnalysisReEntersFromEveryCutPointWithoutRepeatingAnEffect(
        AnalysisCase):
    """Fault cuts: ending notification -> analysis intent -> possible analysis
    launch -> report publication -> owner delivery."""

    def test_a_crash_between_the_failure_and_the_intent_resumes(self):
        failed = self.failed_attempt()
        classified = failure_analysis.classified_failure(
            self.control, failed["attempt_id"], declaration=self.declaration)
        record = failure_analysis.record_failure(
            self.jobs, classified=classified, job_id="job-a",
            stage_id="job-a/implementation", episode=1)
        key = record["failure_key"]
        self.assertIsNone(failure_analysis.intent_of(self.jobs, key))
        self.assertEqual(failure_analysis.recovery_disposition(self.jobs, key),
                         "analysis-owed")
        store = self.reopened()
        seen = self.observed(failed, store=store, now=LATER)
        self.assertEqual(seen["failure"], record)
        self.assertEqual(seen["intent"]["deadlines"]["admitted_at"], LATER)
        self.assertEqual(len(self.journal(failure_analysis.FAILURE_KIND)), 1)

    def test_a_crash_before_the_dispatch_leaves_the_intent_dispatchable(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        store = self.reopened()
        self.assertEqual(
            failure_analysis.reconciled_dispatch(store, self.control,
                                                 key)["state"], "none")
        analysis = self.analysed_attempt(
            1, report=analysis_report(key, seen["intent"]["input_digest"]))
        held = failure_analysis.admit_dispatch(
            store, self.control, key=key, analysis_attempt_id=analysis,
            now=LATER)
        self.assertEqual(held["analysis_attempt_id"], analysis)
        # THE ADMITTED DEADLINE IS THE FIRST ADMISSION'S, not this clock's.
        self.assertEqual(
            failure_analysis.intent_of(store, key)["deadlines"]["admitted_at"],
            NOW)

    def test_a_crash_after_a_launch_the_control_store_holds_reconciles(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        analysis = self.analysed_attempt(
            1, report=analysis_report(key, seen["intent"]["input_digest"]))
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=analysis, now=NOW)
        store = self.reopened()
        reconciled = failure_analysis.reconciled_dispatch(store, self.control,
                                                          key)
        self.assertEqual(reconciled["state"], "launched")
        self.assertEqual(reconciled["analysis_attempt_id"], analysis)
        again = failure_analysis.admit_dispatch(
            store, self.control, key=key, analysis_attempt_id=analysis,
            now=LATER)
        self.assertEqual(again["intended_at"], NOW)
        self.assertEqual(len(self.journal(failure_analysis.DISPATCH_KIND)), 1)

    def test_a_dispatch_the_control_store_cannot_account_for_HOLDS(self):
        """The lost-launch cut. Unknown is a hold, never a redispatch."""
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        failure_analysis.record_dispatch(
            self.jobs, key=key, analysis_attempt_id="analysis-attempt-lost",
            intended_at=NOW)
        reconciled = failure_analysis.reconciled_dispatch(
            self.jobs, self.control, key)
        self.assertEqual(reconciled["state"], "unknown")
        self.assertIn("no second one is ordered", reconciled["why"])
        held = self.refusal(failure_analysis.admit_dispatch, self.jobs,
                            self.control, key=key,
                            analysis_attempt_id="analysis-attempt-2",
                            now=LATER)
        self.assertEqual(held.category, "ambiguous")
        self.assertEqual(len(self.journal(failure_analysis.DISPATCH_KIND)), 1)
        # AND NO REPORT IS READ FROM AN UNRECONCILED EXECUTION EITHER.
        self.assertIn("no reconciled analysis execution to read a report "
                      "from; its dispatch is 'unknown'",
                      str(self.refusal(failure_analysis.deliver_analysis,
                                       self.jobs, self.control, key=key,
                                       destination=OWNER, now=LATER)))

    def test_a_crash_between_the_report_and_the_delivery_finishes(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        report = analysis_report(key, seen["intent"]["input_digest"])
        analysis = self.analysed_attempt(1, report=report)
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=analysis, now=NOW)
        frozen = self.control._connection.execute(
            "SELECT result_id, disposition, manifest_digest FROM outputs "
            "WHERE runtime_attempt_id = ?", (analysis,)).fetchone()
        failure_analysis.record_analysis_report(
            self.jobs, key=key, analysis_attempt_id=analysis, report=report,
            result_id=frozen["result_id"],
            manifest_digest=frozen["manifest_digest"],
            outputs=["analysis", "partial"], ending=frozen["disposition"])
        self.assertEqual(failure_analysis.recovery_disposition(self.jobs, key),
                         "analysis-reported")
        store = self.reopened()
        delivered = failure_analysis.deliver_analysis(
            store, self.control, key=key, destination=OWNER, now=LATER)
        self.assertEqual(delivered["owner_item"]["outcome"], "reported")
        self.assertEqual(len(self.journal(failure_analysis.REPORT_KIND)), 1)
        self.assertEqual(
            len(self.journal(failure_analysis.OWNER_ITEM_KIND)), 1)

    def test_a_reopened_manager_reads_the_delivered_item_and_stops(self):
        held = self.whole_path()
        store = self.reopened()
        seen = self.observed(held["failed"], store=store, now=LATER)
        self.assertEqual(seen["owner_item"]["outcome"], "reported")
        self.assertEqual(seen["disposition"], "delivered")
        self.assertEqual(
            len(self.journal(failure_analysis.OWNER_ITEM_KIND)), 1)


# -- 7. the finite endings ---------------------------------------------------


class AFiniteAnalysisEndsOnceAndGoesDirectlyToTheOwner(AnalysisCase):
    """Analysis failure, expiry or cancellation preserves partials and
    notifies the owner, with no retry and no recursive analysis."""

    def admitted(self, number=1):
        failed = self.failed_attempt(number)
        seen = self.observed(failed, episode=number)
        return failed, seen, seen["failure"]["failure_key"]

    def test_a_partial_analysis_failure_preserves_what_it_wrote(self):
        _failed, seen, key = self.admitted()
        attempt_id = "analysis-attempt-1"
        self.attempt(attempt_id, 1, ANALYST, "analysis-principal-1")
        self.completed(attempt_id)
        place, content = self._custody_tree(attempt_id, "partial",
                                            b"read 2 of 7 locators\n")
        self._frozen(attempt_id, disposition="unable", outputs=[
            self._output(attempt_id, failure_analysis.PARTIAL_OUTPUT,
                         kind="directory-result", content=content,
                         metadata={}, locator="file://" + place)],
                     participant=ANALYST)
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=attempt_id,
                                        now=NOW)
        held = failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-failed",
            why="the analysis ended unable after reading two locators",
            destination=OWNER, now=LATER)
        item = held["owner_item"]
        self.assertEqual(item["outcome"], "analysis-failed")
        self.assertIsNone(item["report_digest"])
        self.assertEqual([one["name"] for one in item["partials"]],
                         ["partial"])
        self.assertEqual(item["partials"][0]["content_digest"],
                         content["tree_digest"])
        self.assertIn("two locators", item["why"])
        self.assertIsNone(failure_analysis.report_of(self.jobs, key))

    def test_expiry_before_dispatch_is_not_dispatched_and_writes_no_partial(self):
        _failed, seen, key = self.admitted()
        analysis = self.analysed_attempt(
            1, report=analysis_report(key, seen["intent"]["input_digest"]))
        held = self.refusal(failure_analysis.admit_dispatch, self.jobs,
                            self.control, key=key,
                            analysis_attempt_id=analysis, now=AFTER_DEADLINE)
        self.assertIn("reached its admitted deadline", str(held))
        self.assertIn("'2026-09-02T01:20:00.000Z'", str(held))
        self.assertEqual(self.journal(failure_analysis.DISPATCH_KIND), [])
        item = failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-expired",
            why="the admitted analysis reached its Job deadline before it "
                "was dispatched", destination=OWNER,
            now=AFTER_DEADLINE)["owner_item"]
        self.assertEqual(item["partials"], [])
        self.assertEqual(item["outcome"], "analysis-expired")

    def test_expiry_mid_turn_preserves_the_partial_the_manager_sealed(self):
        _failed, seen, key = self.admitted()
        attempt_id = "analysis-attempt-1"
        self.attempt(attempt_id, 1, ANALYST, "analysis-principal-1")
        self.completed(attempt_id)
        place, content = self._custody_tree(attempt_id, "partial",
                                            b"stopped at the deadline\n")
        self._frozen(attempt_id, disposition="cancelled", outputs=[
            self._output(attempt_id, failure_analysis.PARTIAL_OUTPUT,
                         kind="directory-result", content=content,
                         metadata={}, locator="file://" + place)],
                     participant=ANALYST)
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=attempt_id,
                                        now=NOW)
        intent = failure_analysis.intent_of(self.jobs, key)
        self.assertFalse(failure_analysis.expiry_reached(intent, LATER))
        self.assertTrue(failure_analysis.expiry_reached(intent,
                                                        AFTER_DEADLINE))
        item = failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-expired",
            why="the analysis turn was still running at the admitted deadline",
            destination=OWNER, now=AFTER_DEADLINE)["owner_item"]
        self.assertEqual([one["name"] for one in item["partials"]],
                         ["partial"])

    def test_a_cancelled_job_admits_no_analysis_and_dispatches_none(self):
        failed = self.failed_attempt()
        self.cancel()
        held = self.refusal(self.observed, failed)
        self.assertIn("not admitted after an explicit cancellation",
                      str(held))
        self.assertEqual(self.journal(failure_analysis.INTENT_KIND), [])
        # A FAILURE ALREADY ATTRIBUTED IS STILL NOT REVIVED INTO A DISPATCH.
        self.assertIsNotNone(failure_analysis.failure_of(
            self.jobs,
            failure_analysis.failure_key(
                authority_uuid=self.AUTHORITY, work_id=WORK_A,
                job_id="job-a", stage_id="job-a/implementation",
                attempt_id=failed["attempt_id"],
                result_id=failed["result_id"])))

    def test_a_cancellation_after_admission_blocks_the_dispatch(self):
        _failed, seen, key = self.admitted()
        analysis = self.analysed_attempt(
            1, report=analysis_report(key, seen["intent"]["input_digest"]))
        self.cancel()
        self.assertIn("not admitted after an explicit cancellation",
                      str(self.refusal(failure_analysis.admit_dispatch,
                                       self.jobs, self.control, key=key,
                                       analysis_attempt_id=analysis,
                                       now=LATER)))
        item = failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-cancelled",
            why="the Job was cancelled before the analysis was dispatched",
            destination=OWNER, now=LATER)["owner_item"]
        self.assertEqual(item["outcome"], "analysis-cancelled")

    def test_an_unaccounted_analysis_cessation_excludes_replacement(self):
        _failed, seen, key = self.admitted()
        failure_analysis.record_dispatch(
            self.jobs, key=key, analysis_attempt_id="analysis-attempt-lost",
            intended_at=NOW)
        item = failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key,
            outcome="analysis-unknown-cessation",
            why="dispatch named analysis-attempt-lost and this manager's "
                "control store accounts for no such attempt",
            destination=OWNER, now=LATER, partials=[])["owner_item"]
        self.assertEqual(item["outcome"], "analysis-unknown-cessation")
        self.assertEqual(item["partials"], [])
        # NO REPLACEMENT. A second dispatch is refused by the delivered item
        # and would be refused by the unknown reconciliation besides.
        self.assertIn("finite analysis",
                      str(self.refusal(failure_analysis.admit_dispatch,
                                       self.jobs, self.control, key=key,
                                       analysis_attempt_id="analysis-2",
                                       now=LATER)))

    def test_every_endpoint_refuses_a_second_intent_dispatch_or_report(self):
        _failed, seen, key = self.admitted()
        failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-failed",
            why="the analysis ended unable", destination=OWNER, now=LATER)
        for call, named in (
                (failure_analysis.record_analysis_intent,
                 {"key": key, "declaration": self.declaration,
                  "admitted_at": LATER}),
                (failure_analysis.record_dispatch,
                 {"key": key, "analysis_attempt_id": "analysis-attempt-2",
                  "intended_at": LATER}),
                (failure_analysis.record_analysis_report,
                 {"key": key, "analysis_attempt_id": "analysis-attempt-2",
                  "report": analysis_report(key,
                                            seen["intent"]["input_digest"]),
                  "result_id": "r", "manifest_digest": "sha256:" + "9" * 64,
                  "outputs": ["analysis"], "ending": "completed"})):
            held = self.refusal(call, self.jobs, **named)
            self.assertEqual(held.category, "policy")
            self.assertIn("automatic retry", str(held))
        self.assertEqual(
            len(self.journal(failure_analysis.OWNER_ITEM_KIND)), 1)

    def test_a_second_endpoint_replays_the_first_owner_item(self):
        _failed, _seen, key = self.admitted()
        one = failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-failed",
            why="the analysis ended unable", destination=OWNER, now=LATER)
        two = failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-expired",
            why="a later observer called it expired", destination=OWNER,
            now=AFTER_DEADLINE)
        self.assertEqual(one["owner_item"], two["owner_item"])
        self.assertEqual(two["owner_item"]["outcome"], "analysis-failed")

    def test_an_endpoint_outcome_outside_the_closed_set_is_refused(self):
        _failed, _seen, key = self.admitted()
        for outcome in ("reported", "retry", "held", None):
            self.assertIn("finite analysis endpoint",
                          str(self.refusal(
                              failure_analysis.deliver_endpoint, self.jobs,
                              self.control, key=key, outcome=outcome,
                              why="x", destination=OWNER, now=LATER)))

    def test_an_endpoint_without_its_reason_is_refused(self):
        _failed, _seen, key = self.admitted()
        self.assertIn("durable text",
                      str(self.refusal(
                          failure_analysis.deliver_endpoint, self.jobs,
                          self.control, key=key, outcome="analysis-failed",
                          why=None, destination=OWNER, now=LATER)))

    def test_an_endpoint_never_carries_a_report_and_a_report_never_a_reason(
            self):
        _failed, seen, key = self.admitted()
        report = analysis_report(key, seen["intent"]["input_digest"])
        self.assertIn("delivers no analysis report",
                      str(self.refusal(
                          failure_analysis.record_owner_item, self.jobs,
                          key=key, outcome="analysis-failed",
                          destination=OWNER, delivered_at=LATER,
                          report=report, why="x")))
        self.assertIn("no separate reason",
                      str(self.refusal(
                          failure_analysis.record_owner_item, self.jobs,
                          key=key, outcome="reported", destination=OWNER,
                          delivered_at=LATER, report=report, why="x")))

    def test_a_reported_item_cannot_be_delivered_without_a_journalled_report(
            self):
        _failed, seen, key = self.admitted()
        self.assertIn("never from a caller's claim about one",
                      str(self.refusal(
                          failure_analysis.record_owner_item, self.jobs,
                          key=key, outcome="reported", destination=OWNER,
                          delivered_at=LATER,
                          report=analysis_report(
                              key, seen["intent"]["input_digest"]))))

    def test_a_preserved_partial_outside_the_permitted_outputs_is_refused(self):
        _failed, _seen, key = self.admitted()
        held = self.refusal(
            failure_analysis.deliver_endpoint, self.jobs, self.control,
            key=key, outcome="analysis-failed", why="x", destination=OWNER,
            now=LATER,
            partials=[{"name": "proposal",
                       "content_digest": "sha256:" + "1" * 64, "bytes": 4}])
        self.assertEqual(held.category, "policy")
        self.assertIn("never permitted to author", str(held))


# -- 8. nothing here mutates anything ----------------------------------------


class NothingHereMutatesTheCandidateVerifierOrExecution(AnalysisCase):

    def _control_bytes(self):
        """Every row of the control store, as bytes, through its own dump."""
        return hashlib.sha256(
            "\n".join(self.control._connection.iterdump()).encode("utf-8")
        ).hexdigest()

    def test_the_whole_path_leaves_the_control_store_byte_identical(self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        report = analysis_report(key, seen["intent"]["input_digest"])
        analysis = self.analysed_attempt(1, report=report)
        before = self._control_bytes()
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=analysis, now=NOW)
        failure_analysis.deliver_analysis(self.jobs, self.control, key=key,
                                          destination=OWNER, now=LATER)
        self.assertEqual(self._control_bytes(), before)

    def test_the_candidate_tree_and_its_result_are_untouched(self):
        held = self.whole_path()
        place = held["failed"]["custody"]
        with open(os.path.join(place, "result.json"), "rb") as handle:
            self.assertEqual(handle.read(), held["failed"]["payload"])
        self.assertEqual(sorted(os.listdir(place)), ["result.json"])

    def test_the_original_failure_record_is_never_rewritten(self):
        failed = self.failed_attempt()
        observed = self.observed(failed)
        key = observed["failure"]["failure_key"]
        before = failure_analysis.failure_of(self.jobs, key)
        failure_analysis.deliver_endpoint(
            self.jobs, self.control, key=key, outcome="analysis-failed",
            why="the analysis ended unable", destination=OWNER, now=LATER)
        after = failure_analysis.failure_of(self.jobs, key)
        self.assertEqual(before, after)
        self.assertEqual(after["disposition"], "analysis-owed")
        # THE ORIGINAL FAILURE AND THE ANALYSIS FAILURE STAY DISTINCT FACTS.
        self.assertEqual(
            failure_analysis.owner_item_of(self.jobs, key)["outcome"],
            "analysis-failed")
        self.assertEqual(after["verification"]["status"], 1)

    def test_evidence_that_changed_under_a_running_analysis_is_not_delivered(
            self):
        failed = self.failed_attempt()
        seen = self.observed(failed)
        key = seen["failure"]["failure_key"]
        analysis = self.analysed_attempt(
            1, report=analysis_report(key, seen["intent"]["input_digest"]))
        failure_analysis.admit_dispatch(self.jobs, self.control, key=key,
                                        analysis_attempt_id=analysis, now=NOW)
        # SOMEBODY REPOINTED THE ORIGINAL EVIDENCE while the analysis ran:
        # the frozen row now names a different retained manifest, whose
        # candidate claim names another object transport. Every binding still
        # holds, so the ending still classifies -- and the fixed input no
        # longer recomposes to what the analysis was admitted on.
        self.repointed(failed, transport="bundle/other.bundle")
        held = self.refusal(failure_analysis.deliver_analysis, self.jobs,
                            self.control, key=key, destination=OWNER,
                            now=LATER)
        self.assertEqual(held.code, "digest")
        self.assertIn("changed under it", str(held))
        self.assertIsNone(failure_analysis.owner_item_of(self.jobs, key))


# -- 9. the cessation axis ---------------------------------------------------


class TheOriginalCessationTravelsWithItsQualification(AnalysisCase):

    def test_an_unaccounted_original_cessation_is_recorded_as_unknown(self):
        held = self.whole_path()
        record = failure_analysis.failure_of(self.jobs, held["key"])
        cessation = record["cessation"]
        self.assertEqual(cessation["answer"], "unknown")
        self.assertTrue(cessation["qualified"])
        self.assertIsNone(cessation["cessation"])
        self.assertIsNone(cessation["component"])
        self.assertEqual(cessation["effects"], [])
        # THE ABSENCE IS NAMED RATHER THAN SUMMARIZED, which is what makes it
        # actionable: an operator is told which records are not there.
        self.assertTrue(
            any(one.startswith("attempt.cessation-*:")
                for one in cessation["absent_records"]))

    def test_a_positively_established_cessation_is_recorded_as_one(self):
        failed = self.failed_attempt()
        said = failure_cause.record_cessation_outcome(
            self.control, failed["attempt_id"], component="expiry-reclaim",
            generation=None, runtime_id="runtime-" + failed["attempt_id"],
            correlation_id="resource.reclaim:w385623", effects=("revoke",),
            outcome="ceased-quiescent")
        self.assertFalse(failure_cause.recording_degraded(said))
        seen = self.observed(failed)
        cessation = seen["failure"]["cessation"]
        self.assertEqual(cessation["answer"], "ceased")
        self.assertFalse(cessation["qualified"])
        self.assertEqual(cessation["component"], "expiry-reclaim")
        self.assertEqual(cessation["cessation"], "quiescent")
        self.assertEqual(cessation["effects"], ["revoke"])
        self.assertIsNotNone(cessation["operation_id"])


# -- 10. no recursion --------------------------------------------------------


class NoRecursiveAnalysisIsEverLaunched(AnalysisCase):
    """"Analysis-role failures are explicitly excluded from recursive
    triggering." Two independent exclusions, because one is configuration and
    the other is history."""

    def analysis_that_failed_verification(self, number=1):
        """One ending that looks exactly like the trigger and is the analyst's."""
        return self.failed_attempt(number, participant=ANALYST)

    def test_the_declared_analysis_participants_own_ending_never_triggers(self):
        failed = self.analysis_that_failed_verification()
        held = self.refusal(failure_analysis.classified_failure, self.control,
                            failed["attempt_id"],
                            declaration=self.declaration)
        self.assertEqual(held.category, "policy")
        self.assertIn("never triggers another analysis", str(held))
        self.refusal(self.observed, failed)
        self.assertEqual(self.journal(failure_analysis.FAILURE_KIND), [])

    def test_a_dispatched_analysis_attempt_is_excluded_by_HISTORY(self):
        """Even under a renamed participant the dispatch record still holds."""
        _held = self.whole_path()
        analysis = "analysis-attempt-1"
        # The dispatched analysis now presents a verification-failed ending of
        # its own, under a declaration that no longer names its participant.
        place, content = self._custody_tree(analysis, "proposal",
                                            worker_result())
        self.control._connection.execute(
            "DELETE FROM outputs WHERE runtime_attempt_id = ?", (analysis,))
        self.control._connection.execute(
            "DELETE FROM output_artifacts WHERE runtime_attempt_id = ?",
            (analysis,))
        metadata = {
            failure_analysis.CANDIDATE_CLAIM: {
                "base": driver.BASE, "head": "f" * 40,
                "transport": "bundle/x", "recap": "x"},
            failure_analysis.ORDINARY_TESTS: {
                "argv": ["true"], "base": driver.BASE, "head": "f" * 40,
                "status": 1, "task_digest": "sha256:" + "7" * 64,
                "task_id": "w385623-fixture-1"}}
        self._frozen(analysis, disposition="unable", outputs=[
            self._output(analysis, "proposal", kind="git-change-proposal",
                         content=content, metadata=metadata,
                         locator="file://" + place)],
                     result_id="result-recursive", participant=ANALYST)
        renamed = analysis_declaration(participant="baton.other-analyst")
        held = self.refusal(
            failure_analysis.observe_terminal_failure, self.jobs,
            self.control, stage_id="job-a/implementation", episode=2,
            attempt_id=analysis, declaration=renamed, now=LATER)
        self.assertEqual(held.category, "policy")
        self.assertIn("is the analysis this store dispatched", str(held))
        self.assertEqual(len(self.journal(failure_analysis.FAILURE_KIND)), 1)
        self.assertEqual(len(self.journal(failure_analysis.INTENT_KIND)), 1)


# -- 11. the owner-approved profile ------------------------------------------


class TheFiniteProfileIsTheOwnersExactPublishedDefinition(unittest.TestCase):
    """M385612's published definition, and nothing this build chose."""

    def test_the_held_definition_is_the_published_bytes(self):
        raw = APPROVED_PROFILE.read_bytes()
        self.assertEqual(failure_analysis.ANALYSIS_DEFINITION_BYTES, raw)
        self.assertEqual(json.loads(raw), failure_analysis.ANALYSIS_DEFINITION)

    def test_the_digest_is_the_one_the_contract_pins(self):
        self.assertEqual(failure_analysis.ANALYSIS_PROFILE_DIGEST,
                         "sha256:" + APPROVED_PROFILE_DIGEST)
        self.assertEqual(
            hashlib.sha256(APPROVED_PROFILE.read_bytes()).hexdigest(),
            APPROVED_PROFILE_DIGEST)

    def test_the_resolved_bounds_and_clock_origins_are_the_approved_ones(self):
        held = failure_analysis.resolved_profile()
        self.assertEqual(held["overall_job_seconds"], 4800)
        self.assertTrue(held["overall_job_includes_queue"])
        self.assertEqual(held["overall_job_origin"], "accepted_admission")
        self.assertEqual(held["stage_seconds"], 4800)
        self.assertEqual(held["stage_origin"], "stage_admission")
        self.assertEqual(held["provider_invocation_seconds"], 3600)
        self.assertEqual(held["provider_invocation_origin"],
                         "invocation_start")
        self.assertEqual(held["automatic_retries"], 0)
        self.assertEqual(held["automatic_corrections"], 0)
        self.assertEqual(held["units"], "seconds")

    def test_a_profile_this_build_does_not_hold_is_refused(self):
        for name in ("stage1-verification-review/1", "documentation/1",
                     job_control.NATIVE_HANDOFF_PROFILE, ""):
            with self.assertRaises(ContractRefusal):
                failure_analysis.resolved_profile(name)

    def test_the_job_deadline_includes_queue_time_from_the_admission(self):
        policy = failure_analysis.resolved_profile()
        held = failure_analysis.admitted_deadlines(policy, admitted_at=NOW)
        self.assertEqual(held["job_deadline_at"], "2026-09-02T01:20:00.000Z")
        self.assertTrue(held["includes_queue"])
        # AND THE STAGE AND PROVIDER CLOCKS ARE NOT DERIVED AT ADMISSION:
        # their origins do not exist yet, and inventing them here would be the
        # "no activity or dispatch timestamp substitutes for an invocation
        # start" rule broken at the first opportunity.
        self.assertNotIn("stage_deadline_at", held)
        self.assertNotIn("provider_deadline_at", held)

    def test_the_implementation_jobs_own_control_profile_is_untouched(self):
        """The analysis profile is the product, not this Job's control."""
        self.assertNotIn(failure_analysis.ANALYSIS_PROFILE,
                         job_control.PROFILES)
        # W385624 ADDED A FOURTH ENTRY and this expectation moved with it:
        # `stage1-verification-review/1` is the owner-approved finite control
        # of a RETAINED-RECOVERY successor, which does run verification
        # commands and so does belong in this table. What the case is about
        # is unchanged and is still checked below -- the ANALYSIS profile is
        # not here, and no existing entry's numbers moved.
        self.assertEqual(sorted(job_control.PROFILES),
                         ["documentation/1", "native-handoff-heavy/1",
                          "native-handoff/1",
                          "stage1-verification-review/1"])
        self.assertEqual(job_control.PROFILES["documentation/1"],
                         {"correction_rounds": 0, "stage_seconds": 4800,
                          "job_seconds": 9960, "provider_turn_seconds": 3600,
                          "verification_command_seconds": 900})
        self.assertEqual(job_control.PROFILES["native-handoff/1"],
                         {"correction_rounds": 0, "stage_seconds": 4800,
                          "job_seconds": 9960, "provider_turn_seconds": 3600,
                          "verification_command_seconds": 900})
        # M385638 separately approved this implementation/review profile;
        # it does not move the analysis definition into Job control.
        self.assertEqual(job_control.PROFILES["native-handoff-heavy/1"],
                         {"correction_rounds": 0, "stage_seconds": 9000,
                          "job_seconds": 21600, "provider_turn_seconds": 7200,
                          "verification_command_seconds": 900})
        # M385612 separately approved the recovery successor's own bounds;
        # it does not move the analysis definition into Job control either.
        self.assertEqual(
            job_control.PROFILES["stage1-verification-review/1"],
            {"correction_rounds": 0, "stage_seconds": 4800,
             "job_seconds": 9960, "provider_turn_seconds": 3600,
             "verification_command_seconds": 900})



# -- 12. the configured production path --------------------------------------
#
# WHAT THESE CASES DRIVE, and it is deliberately not a helper. Every one of
# them calls the REAL `manager.sweep` -- the tick `tools/job_manager.py serve`
# and `--once` run, and the one `reconcile` resumes with -- over a real Job
# store holding a real SETTLED ending, with the declared analysis worker
# produced by the product's own producer out of deployment configuration. The
# trigger, the dispatch and the owner delivery all happen because the tick
# derived that they were owed; nothing below calls
# `observe_terminal_failure`, `admit_dispatch`, `deliver_analysis` or
# `deliver_endpoint`.
#
# WHAT IS FAKED, AND ONLY AT ITS NORMAL BOUNDARY: the DEPLOYMENT, which is
# `fixtures.FakeOperations` -- the same stand-in `test_sweep` drives the tick
# with, and whose composition against the real operations object is
# `test_delegation`'s -- and the analysis worker's TURN, which is a
# deterministic replay that writes its result into the real control store and
# real custody. There is no provider, model, adapter, image or container here.
#
# WHAT IS REAL: the Job store, its stages and episodes, its real
# `ending.register_ending`/`settle_ending` records, its cancellation fence,
# its operations journal, the control store, the attempts, the retained result
# manifests, the measured trees on disk-backed storage, the composed typed
# failure cause, and every act of `failure_analysis`.


class ReplayAnalyst:
    """The declared analysis worker's turn, replayed deterministically.

    THE NORMAL PROVIDER BOUNDARY AND NOTHING ABOVE IT. In production this is
    `stage_execution.RecoveryAnalysis.launch`, which composes a container over
    the configured worker deployment; what the Job manager's pass requires of
    it is exactly what this does -- order or re-enter ONE attempt identity's
    own turn, and leave its result in the control store for the manager to
    read. The pass never reads a value this returns.

    `in_flight` IS HOW A RUNNING ANALYSIS IS EXPRESSED: the attempt row
    appears on the first order -- which is what makes the dispatch
    `launched` rather than `unknown` -- and the frozen result only after that
    many further re-entries.

    `lands=False` IS THE LOST LAUNCH: the order is observed and no attempt
    ever appears, which is the fault cut "after possible launch with lost
    reply".
    """

    def __init__(self, case, *, report=None, disposition="completed",
                 partial=True, outputs=None, lands=True, in_flight=0):
        self.case = case
        self.report = report
        self.disposition = disposition
        self.partial = partial
        self.outputs = outputs
        self.lands = lands
        self.in_flight = in_flight
        self.orders = []

    def __call__(self, *, attempt_id, document, intent):
        self.orders.append({"attempt_id": attempt_id,
                            "input_digest":
                                failure_analysis.input_digest(document),
                            "failure_key": document["failure_key"],
                            "job_id": intent["job_id"],
                            "participant": intent["participant"],
                            "deadline": intent["deadlines"]["job_deadline_at"]})
        if not self.lands:
            return None
        if len(self.orders) == 1:
            self.case.attempt(attempt_id, 9, ANALYST,
                              "analysis-principal-production")
        if len(self.orders) <= self.in_flight:
            return None
        if self.case.frozen_already(attempt_id):
            return None
        report = self.report if self.report is not None else analysis_report(
            document["failure_key"], failure_analysis.input_digest(document))
        self.case.completed(attempt_id)
        self.case._frozen(
            attempt_id, disposition=self.disposition,
            outputs=(self.outputs if self.outputs is not None
                     else self.case.analysis_outputs(
                         attempt_id, report=report, partial=self.partial)),
            participant=ANALYST, generation=9)
        return None


class Seam:
    """One deployment's configured analysis seam, in the product's own shape.

    The four members `failure_analysis.ANALYSIS_SEAM` names and nothing else.
    `stage_execution.RecoveryAnalysis` is the production one; this is the same
    surface with the container behind `launch` replaced by the replay above.
    """

    def __init__(self, control, declaration, destination, launch):
        self.control = control
        self.declaration = declaration
        self.destination = destination
        self.launch = launch


DEPLOYMENT_DECLARED = {"worker_id": "analysis-worker-1",
                       "participant": ANALYST,
                       "principal": ANALYST_PRINCIPAL,
                       "capability_digest": "sha256:" + "c" * 64}


class ProductionCase(AnalysisCase):
    """One Job whose implementation stage really settled a failed ending."""

    def setUp(self):
        super().setUp()
        # THE DECLARATION IS PRODUCED, NOT WRITTEN. This is the deployment
        # producer under test: four facts a deployment knows, and the schema,
        # the role, the owner-approved profile, its digest and the permitted
        # outputs filled in by the product.
        self.declaration = failure_analysis.declared_analysis_worker(
            dict(DEPLOYMENT_DECLARED))
        self.analyst = ReplayAnalyst(self)
        self.acts = fixtures.FakeOperations(authority_uuid=self.AUTHORITY)
        self.acts.recovery_analysis = Seam(self.control, self.declaration,
                                           OWNER, self.analyst)

    # -- the real settled ending ---------------------------------------------

    def frozen_already(self, attempt_id):
        return self.control._connection.execute(
            "SELECT 1 FROM outputs WHERE runtime_attempt_id = ?",
            (attempt_id,)).fetchone() is not None

    def episode_view(self, stage_id="job-a/implementation", store=None):
        store = store if store is not None else self.jobs
        row = {one["stage_id"]: one
               for one in submission.stage_rows(store)}[stage_id]
        return episodes.attempting(row, episodes.live_of(store, stage_id))

    def assignment(self, generation=1, participant=WRITER):
        return {"work_ref": {"authority_uuid": self.AUTHORITY,
                             "work_id": WORK_A},
                "participant": participant, "generation": generation}

    def settled(self, *, stage_id="job-a/implementation", generation=1,
                settle=True, disposition="unable", participant=WRITER,
                store=None, **changed):
        """Retain one real terminal ending AND journal its real settlement.

        THE CONTROL-STORE ATTEMPT IS THE EPISODE'S OWN. The production pass
        derives what it observes from the Job store's settled ending records,
        whose selectors are the episode's derived identities -- so a case that
        retained its attempt under a name of its own would be driving the pass
        against an ending no store holds.
        """
        store = store if store is not None else self.jobs
        view = self.episode_view(stage_id, store=store)
        fixed = self.assignment(generation, participant)
        failed = self.failed_attempt(generation, attempt_id=view["attempt_id"],
                                     participant=participant, **changed)
        ending.register_ending(
            store, view, assignment=fixed, disposition=disposition,
            terminal_manifest_digest=failed["manifest"],
            retention_disposition="retain",
            retention_policy_digest="sha256:" + "9" * 64)
        if settle:
            ending.settle_ending(
                store, view, assignment=fixed,
                evidence={"result_id": failed["result_id"],
                          "manifest_digest": failed["manifest"],
                          "receipt_digest": "sha256:" + "8" * 64})
        return failed

    # -- the production tick -------------------------------------------------

    def tick(self, now=NOW, store=None, acts=None):
        return sweep(store if store is not None else self.jobs,
                     acts if acts is not None else self.acts, now=now)

    def analysed(self, report):
        return [(one["act"], one["outcome"],
                 (one.get("detail") or {}).get("owner_item")
                 or (one.get("detail") or {}).get("disposition")
                 or (one.get("detail") or {}).get("category")
                 or (one.get("detail") or {}).get("state"))
                for one in report.get("analysed", [])]

    def only_key(self, store=None):
        held = failure_analysis.failures_of(store if store is not None
                                            else self.jobs)
        self.assertEqual(len(held), 1, held)
        return sorted(held)[0]

    def driven(self, *, instants=(NOW, LATER), store=None, acts=None):
        """Tick until the recovery path has nothing left to do."""
        reports = []
        for instant in instants:
            reports.append(self.tick(instant, store=store, acts=acts))
        return reports


class TheRealTickTriggersDispatchesAndDeliversWithoutACourier(ProductionCase):
    """The correction's whole point: nobody calls the path by hand."""

    def test_three_ticks_observe_dispatch_and_deliver_one_owner_item(self):
        failed = self.settled()
        first, second = self.driven()
        self.assertEqual(
            self.analysed(first),
            [("observe", "observed", "analysis-intended"),
             ("dispatch", "dispatched", "analysis-dispatched")])
        self.assertEqual(self.analysed(second),
                         [("deliver", "delivered", "reported")])
        key = self.only_key()
        # EVERY ONE OF THE FIVE RECORDS EXISTS, and each exactly once --
        # written by the tick and not by this case.
        for kind in (failure_analysis.FAILURE_KIND,
                     failure_analysis.INTENT_KIND,
                     failure_analysis.DISPATCH_KIND,
                     failure_analysis.REPORT_KIND,
                     failure_analysis.OWNER_ITEM_KIND):
            self.assertEqual(len(self.journal(kind)), 1, kind)
        item = failure_analysis.owner_item_of(self.jobs, key)
        self.assertEqual(item["outcome"], "reported")
        self.assertEqual(item["destination"], OWNER)
        self.assertEqual(item["delivered_at"], LATER)
        self.assertEqual(failure_analysis.recovery_disposition(self.jobs, key),
                         "delivered")
        # AND THE ANALYSIS REALLY RAN, ordered once, over the exact evidence.
        self.assertEqual(len(self.analyst.orders), 1)
        order = self.analyst.orders[0]
        self.assertEqual(order["failure_key"], key)
        self.assertEqual(order["attempt_id"],
                         failure_analysis.analysis_attempt_id(key))
        self.assertEqual(
            order["input_digest"],
            failure_analysis.failure_of(self.jobs, key)["input_digest"])
        self.assertEqual(order["participant"], ANALYST)
        self.assertEqual(order["job_id"], "job-a")
        self.assertEqual(order["attempt_id"],
                         "analysis-" + key[len("sha256:"):])
        del failed

    def test_the_delivered_failure_names_the_exact_retained_lineage(self):
        failed = self.settled()
        self.driven()
        key = self.only_key()
        record = failure_analysis.failure_of(self.jobs, key)
        self.assertEqual(record["selectors"],
                         {"authority_uuid": self.AUTHORITY,
                          "work_id": WORK_A, "job_id": "job-a",
                          "stage_id": "job-a/implementation", "episode": 1,
                          "attempt_id": failed["attempt_id"],
                          "result_id": failed["result_id"]})
        self.assertEqual(record["episode"], 1)
        # AND THE KEY IS OVER THE SIX THE CONTRACT NAMES, which is not the
        # same set: the episode travels in the record so a reader can resolve
        # the round, and a renewed failure in a later episode of the same
        # stage is a different ATTEMPT and so a different key already.
        self.assertEqual(
            key,
            failure_analysis.failure_key(
                **{name: record["selectors"][name]
                   for name in failure_analysis.FAILURE_SELECTORS}))
        self.assertEqual(record["candidate"]["base"], driver.BASE)
        self.assertEqual(record["candidate"]["tree_digest"],
                         failed["content"]["tree_digest"])
        self.assertEqual(record["verification"]["status"], 1)
        self.assertEqual(record["verification"]["argv"][-1],
                         "exec python3 -m unittest -v x\n")
        self.assertEqual(record["execution"]["participant"], WRITER)
        # THE ORIGINAL ENDING IS UNTOUCHED BY ALL OF IT.
        held = ending.ending_of(self.jobs, "job-a/implementation", 1)
        self.assertEqual(held["intent"]["disposition"], "unable")
        self.assertEqual(held["settlement"]["evidence"]["result_id"],
                         failed["result_id"])

    def test_the_admitted_analysis_carries_the_owner_approved_profile(self):
        self.settled()
        self.tick()
        intent = failure_analysis.intent_of(self.jobs, self.only_key())
        self.assertEqual(intent["profile"], failure_analysis.ANALYSIS_PROFILE)
        self.assertEqual(intent["profile_digest"],
                         "sha256:" + APPROVED_PROFILE_DIGEST)
        self.assertEqual(intent["policy"]["overall_job_seconds"], 4800)
        self.assertEqual(intent["policy"]["automatic_retries"], 0)
        self.assertEqual(intent["deadlines"]["admitted_at"], NOW)
        self.assertEqual(intent["deadlines"]["job_deadline_at"],
                         "2026-09-02T01:20:00.000Z")
        self.assertEqual(intent["role"], failure_analysis.ANALYSIS_ROLE)
        self.assertEqual(intent["participant"], ANALYST)
        self.assertEqual(intent["principal"], ANALYST_PRINCIPAL)
        self.assertEqual(self.analyst.orders[0]["deadline"],
                         "2026-09-02T01:20:00.000Z")

    def test_the_resume_path_reaches_the_same_pass(self):
        """`reconcile` is what a restarted serving process runs first."""
        self.settled()
        report = manager.reconcile(self.jobs, self.acts, now=NOW)
        self.assertEqual(
            self.analysed(report),
            [("observe", "observed", "analysis-intended"),
             ("dispatch", "dispatched", "analysis-dispatched")])
        self.assertIn(("recover", NOW), self.acts.calls)

    def real_operations(self, seam=None):
        """The REAL operations surface, with the seam as its capability.

        Not a fake: `ManagerOperations` over this case's own control store and
        an Authority-bound port, which is the object a deployment composes
        and the one `test_delegation` proves the closed surface against.
        """
        from baton_v12.job_manager import ManagerOperations
        from baton_v12.worker_manager import AuthorityPort

        session = fixtures.FakeSession()
        session.open_work(WORK_A)
        return ManagerOperations(
            self.control, AuthorityPort(session, fixtures.fake_claim_signature),
            mint_bearer=lambda: "bearer-1",
            deliver_bearer=lambda issued: None,
            recovery_analysis=(seam if seam is not None
                               else self.acts.recovery_analysis))

    def test_the_real_operations_surface_drives_the_whole_path(self):
        """THE PRODUCTION SURFACE, not a stand-in for it.

        The same two ticks, through `ManagerOperations` with a real
        Authority-bound port: the ordinary stage act is admitted for real
        alongside the recovery pass, one analysis is ordered, and one owner
        item is delivered.
        """
        acts = self.real_operations()
        self.settled()
        first, second = self.driven(acts=acts)
        self.assertEqual(
            self.analysed(first),
            [("observe", "observed", "analysis-intended"),
             ("dispatch", "dispatched", "analysis-dispatched")])
        self.assertEqual(
            [(one["stage_id"], one["act"], one["outcome"])
             for one in first["acts"]],
            [("job-a/implementation", "admit", "performed")])
        self.assertEqual(self.analysed(second),
                         [("deliver", "delivered", "reported")])
        key = self.only_key()
        self.assertEqual(
            failure_analysis.owner_item_of(self.jobs, key)["outcome"],
            "reported")
        self.assertEqual(len(self.analyst.orders), 1)
        self.assertEqual(self.analyst.orders[0]["attempt_id"],
                         failure_analysis.analysis_attempt_id(key))

    def test_the_real_operations_object_carries_the_capability(self):
        """The seam is a member of the surface a deployment supplies.

        Not an attribute this suite invented on a fake: `ManagerOperations`
        takes it as an optional capability beside the runtime start and the
        exchange halves, and `manager._analyse` finds it there.
        """
        from baton_v12.job_manager import ManagerOperations

        seam = Seam(self.control, self.declaration, OWNER, self.analyst)
        acts = ManagerOperations(self.control, None, mint_bearer=lambda: "b",
                                 deliver_bearer=lambda one: None,
                                 recovery_analysis=seam)
        self.assertIs(acts.recovery_analysis, seam)
        self.assertIsNone(
            ManagerOperations(self.control, None, mint_bearer=lambda: "b",
                              deliver_bearer=lambda one: None)
            .recovery_analysis)


class ADeploymentThatDeclaresNoAnalystAnalysesNothing(ProductionCase):
    """What preserves every accepted deployment in this tree."""

    def test_a_tick_with_no_seam_observes_no_failure_at_all(self):
        self.settled()
        bare = fixtures.FakeOperations(authority_uuid=self.AUTHORITY)
        report = sweep(self.jobs, bare, now=NOW)
        self.assertNotIn("analysed", report)
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})
        self.assertEqual(self.journal(failure_analysis.FAILURE_KIND), [])
        self.assertEqual(self.analyst.orders, [])

    def test_a_tick_with_no_retained_failure_reports_nothing(self):
        report = self.tick()
        self.assertNotIn("analysed", report)
        self.assertEqual(self.analyst.orders, [])

    def test_a_misconfigured_seam_is_a_condition_and_not_a_fault(self):
        """One broken recovery configuration must not stop the tick."""
        self.settled()
        self.acts.recovery_analysis = Seam(
            self.control,
            analysis_declaration(profile="stage1-analysis/2"), OWNER,
            self.analyst)
        report = self.tick()
        self.assertEqual(self.analysed(report),
                         [("observe", "refused", "policy")])
        # THE REST OF THE TICK HAPPENED. The ordinary stage act is still
        # derived and delegated, which is the whole point of containing it.
        self.assertEqual([one["act"] for one in report["acts"]], ["admit"])
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})

    def test_a_seam_missing_a_member_refuses_before_anything_is_spent(self):
        self.settled()
        self.acts.recovery_analysis = Seam(self.control, self.declaration,
                                           OWNER, None)
        report = self.tick()
        self.assertEqual(self.analysed(report),
                         [("observe", "refused", "refused")])
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})


class OnlyASettledProducerFailureIsObserved(ProductionCase):
    """The pass selects endings; it does not accept them."""

    def test_a_registered_but_unsettled_ending_is_not_yet_attributed(self):
        self.settled(settle=False)
        report = self.tick()
        self.assertNotIn("analysed", report)
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})
        self.assertEqual(
            failure_analysis.settled_trigger_endings(self.jobs), [])
        # AND IT IS OBSERVED ONCE IT SETTLES, from the same durable records.
        view = self.episode_view()
        ending.settle_ending(
            self.jobs, view, assignment=self.assignment(),
            evidence={"result_id": "result-" + view["attempt_id"],
                      "manifest_digest": "sha256:" + "1" * 64,
                      "receipt_digest": "sha256:" + "8" * 64})
        self.assertEqual(self.analysed(self.tick()),
                         [("observe", "observed", "analysis-intended"),
                          ("dispatch", "dispatched", "analysis-dispatched")])

    def test_a_completed_ending_is_not_this_trigger(self):
        self.settled(disposition="completed", ending="candidate", status=0,
                     verification={"status": 0})
        report = self.tick()
        self.assertNotIn("analysed", report)
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})

    def test_a_provider_failure_is_not_this_trigger(self):
        self.settled(ending="provider-failed",
                     provider={"ok": False, "reason": "timeout",
                               "seconds_bound": 3600,
                               "seconds_bound_source": "job-selected"})
        report = self.tick()
        self.assertNotIn("analysed", report)
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})

    def test_a_review_stage_ending_is_not_a_producer_ending(self):
        self.settled(stage_id="job-a/review")
        report = self.tick()
        self.assertNotIn("analysed", report)
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})

    def test_an_invalid_retained_candidate_is_reported_and_never_used(self):
        """REC-8: reported, and not recovery input."""
        failed = self.settled()
        self.repointed(failed, head="0" * 40)
        report = self.tick()
        self.assertEqual(self.analysed(report), [("observe", "refused",
                                                  "ambiguous")])
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})
        self.assertEqual(self.analyst.orders, [])
        # AND IT IS REPORTED AGAIN rather than forgotten, because the pass is
        # level-triggered and the cause has not been disposed of.
        self.assertEqual(self.analysed(self.tick(LATER)),
                         [("observe", "refused", "ambiguous")])


class OneEndingIsOneAnalysisHoweverManyTicksRun(ProductionCase):
    """The duplicate rule, proved against the production loop."""

    def test_ten_ticks_order_one_turn_and_deliver_one_item(self):
        self.settled()
        for number in range(10):
            self.tick(f"2026-09-02T00:0{number}:00.000Z")
        key = self.only_key()
        self.assertEqual(len(self.analyst.orders), 1)
        self.assertEqual(len(self.journal(failure_analysis.OWNER_ITEM_KIND)),
                         1)
        self.assertEqual(len(self.journal(failure_analysis.DISPATCH_KIND)), 1)
        self.assertEqual(failure_analysis.owner_item_of(self.jobs,
                                                        key)["outcome"],
                         "reported")
        # AND A DELIVERED RECOVERY STOPS BEING REPORTED, so a tick report
        # names acts rather than a growing history.
        self.assertNotIn("analysed", self.tick(LATER))

    def test_a_second_incarnation_continues_from_the_durable_records(self):
        """The restart cut, driven through two real tick processes."""
        self.settled()
        self.assertEqual(
            self.analysed(self.tick()),
            [("observe", "observed", "analysis-intended"),
             ("dispatch", "dispatched", "analysis-dispatched")])
        reopened = self.reopened()
        acts = fixtures.FakeOperations(authority_uuid=self.AUTHORITY)
        acts.recovery_analysis = Seam(self.control, self.declaration, OWNER,
                                      self.analyst)
        self.assertEqual(self.analysed(self.tick(LATER, store=reopened,
                                                 acts=acts)),
                         [("deliver", "delivered", "reported")])
        key = self.only_key(store=reopened)
        self.assertEqual(len(self.analyst.orders), 1)
        self.assertEqual(
            failure_analysis.recovery_disposition(reopened, key), "delivered")

    def test_an_in_flight_analysis_is_re_entered_under_one_identity(self):
        """Level-triggered, exactly as a stage's runtime start is."""
        self.analyst.in_flight = 3
        self.settled()
        instants = ["2026-09-02T00:0%d:00.000Z" % one for one in range(6)]
        held = [self.analysed(self.tick(one)) for one in instants]
        self.assertEqual(held[1], [("deliver", "held", "launched")])
        self.assertEqual(held[2], [("deliver", "held", "launched")])
        self.assertEqual(held[4], [("deliver", "delivered", "reported")])
        # FOUR ORDERS, ONE IDENTITY, ONE DISPATCH RECORD.
        key = self.only_key()
        self.assertEqual({one["attempt_id"] for one in self.analyst.orders},
                         {failure_analysis.analysis_attempt_id(key)})
        self.assertEqual(len(self.journal(failure_analysis.DISPATCH_KIND)), 1)
        self.assertEqual(len(self.analyst.orders), 4)


class TheFiniteEndingsAreReachedByTheTickItself(ProductionCase):
    """Four finite endings, each delivered automatically and exactly once."""

    def test_a_failed_analysis_delivers_analysis_failed_with_its_partials(
            self):
        self.analyst.disposition = "unable"
        self.settled()
        reports = self.driven()
        self.assertEqual(self.analysed(reports[1]),
                         [("deliver", "delivered", "analysis-failed")])
        item = failure_analysis.owner_item_of(self.jobs, self.only_key())
        self.assertEqual(item["outcome"], "analysis-failed")
        self.assertIsNone(item["report_digest"])
        self.assertEqual([one["name"] for one in item["partials"]],
                         ["analysis", "partial"])
        self.assertIn("unable", item["why"])
        self.assertIsNone(failure_analysis.report_of(self.jobs,
                                                     self.only_key()))

    def test_a_cancelled_analysis_execution_delivers_analysis_cancelled(self):
        self.analyst.disposition = "cancelled"
        self.settled()
        self.driven()
        self.assertEqual(
            failure_analysis.owner_item_of(self.jobs,
                                           self.only_key())["outcome"],
            "analysis-cancelled")

    def test_a_cancelled_job_is_never_admitted_or_dispatched(self):
        """A cancelled Job earns no analysis admission, ever."""
        self.settled()
        self.cancel()
        report = self.tick()
        # THE ENDING IS STILL ATTRIBUTED -- it happened, and the failure item
        # is this manager's durable account of it -- and the ADMISSION
        # refuses, so no analysis exists to order and nothing was spent.
        self.assertEqual(self.analysed(report), [("observe", "refused",
                                                  "refused")])
        self.assertEqual(self.analyst.orders, [])
        key = self.only_key()
        self.assertIsNotNone(failure_analysis.failure_of(self.jobs, key))
        self.assertIsNone(failure_analysis.intent_of(self.jobs, key))
        self.assertIsNone(failure_analysis.owner_item_of(self.jobs, key))
        self.assertEqual(failure_analysis.recovery_disposition(self.jobs, key),
                         "analysis-owed")
        # AND IT IS HELD VISIBLY RATHER THAN DISAPPEARING: a recovery that can
        # never be advanced is named on every later tick.
        self.assertEqual(self.analysed(self.tick(LATER)),
                         [("observe", "held", "analysis-owed")])
        self.assertEqual(self.analyst.orders, [])

    def test_a_job_cancelled_after_admission_delivers_analysis_cancelled(self):
        self.analyst.in_flight = 5
        self.settled()
        self.tick()
        self.cancel()
        report = self.tick(LATER)
        self.assertEqual(self.analysed(report),
                         [("deliver", "delivered", "analysis-cancelled")])
        item = failure_analysis.owner_item_of(self.jobs, self.only_key())
        self.assertEqual(item["outcome"], "analysis-cancelled")
        self.assertIn("cancelled", item["why"])

    def test_expiry_before_any_dispatch_delivers_analysis_expired(self):
        """Admitted, never dispatched, and the admitted bound decides.

        THE DISPATCH IS HELD BY SOMETHING REAL: the retained evidence is
        repointed after the ending was attributed, so the revalidation every
        dispatch performs refuses rather than sending an agent a diagnosis
        about evidence that changed under its intent. Then the owner-approved
        4800-second Job bound -- queue time included -- passes, and the pass
        delivers the one owner item an unstarted analysis is owed.
        """
        self.settled()
        # THE DERIVED ANALYSIS IDENTITY IS ALREADY SOMEBODY ELSE'S. The key is
        # a digest over the ending's six selectors, so this case can derive it
        # before the tick does and retain a foreign attempt under it: the
        # dispatch then refuses rather than binding this failure's analysis to
        # another participant's execution, and refuses BEFORE it records
        # anything. Nothing is spent and the admission stands.
        view = self.episode_view()
        frozen = self.control._connection.execute(
            "SELECT result_id FROM outputs WHERE runtime_attempt_id = ?",
            (view["attempt_id"],)).fetchone()
        key = failure_analysis.failure_key(
            authority_uuid=self.AUTHORITY, work_id=WORK_A, job_id="job-a",
            stage_id="job-a/implementation", attempt_id=view["attempt_id"],
            result_id=frozen["result_id"])
        self.attempt(failure_analysis.analysis_attempt_id(key), 7, WRITER,
                     "writer-principal-7")
        self.assertEqual(self.analysed(self.tick()),
                         [("observe", "observed", "analysis-intended"),
                          ("dispatch", "refused", "integrity")])
        self.assertEqual(self.only_key(), key)
        self.assertEqual(len(self.journal(failure_analysis.INTENT_KIND)), 1)
        self.assertEqual(self.journal(failure_analysis.DISPATCH_KIND), [])
        self.assertEqual(self.analyst.orders, [])
        report = self.tick(AFTER_DEADLINE)
        self.assertEqual(self.analysed(report),
                         [("deliver", "delivered", "analysis-expired")])
        item = failure_analysis.owner_item_of(self.jobs, key)
        self.assertEqual(item["outcome"], "analysis-expired")
        self.assertEqual(item["partials"], [])
        self.assertIn("before its analysis was dispatched", item["why"])
        self.assertEqual(self.journal(failure_analysis.DISPATCH_KIND), [])
        self.assertEqual(self.analyst.orders, [])

    def test_the_original_jobs_own_expiry_mid_turn_is_reported_as_expiry(self):
        """A Job expiry and a cancellation are two acts, and two words.

        The fence this reaches is the one `job_control` journalled when the
        ORIGINAL Job's own stage deadline passed. It is read before the
        analysis's admitted bound and it names what happened -- an expiry --
        rather than reporting the owner as having cancelled something.
        """
        self.analyst.in_flight = 20
        self.settled()
        self.tick()
        report = self.tick(AFTER_DEADLINE)
        self.assertEqual(self.analysed(report),
                         [("deliver", "delivered", "analysis-expired")])
        item = failure_analysis.owner_item_of(self.jobs, self.only_key())
        self.assertEqual(item["outcome"], "analysis-expired")
        self.assertIn("expired", item["why"])
        self.assertNotIn("cancelled", item["why"])

    def test_a_finite_ending_is_never_retried_by_a_later_tick(self):
        self.analyst.disposition = "unable"
        self.settled()
        self.driven()
        before = len(self.analyst.orders)
        for instant in (AFTER_DEADLINE, "2026-09-02T03:00:00.000Z"):
            self.assertNotIn("analysed", self.tick(instant))
        self.assertEqual(len(self.analyst.orders), before)
        self.assertEqual(len(self.journal(failure_analysis.OWNER_ITEM_KIND)),
                         1)


class TheProductionPassMutatesNothingItReads(ProductionCase):
    """The no-mutation ruling, proved over the whole automatic path."""

    def test_the_original_candidate_custody_and_ending_are_unchanged(self):
        failed = self.settled()
        before = pathlib.Path(
            os.path.join(failed["custody"], "result.json")).read_bytes()
        held = ending.ending_of(self.jobs, "job-a/implementation", 1)
        self.driven()
        self.assertEqual(
            pathlib.Path(os.path.join(failed["custody"],
                                      "result.json")).read_bytes(), before)
        self.assertEqual(ending.ending_of(self.jobs, "job-a/implementation",
                                          1), held)
        # AND NO SUCCESSOR, FRESH ATTEMPT OR CORRECTION WAS OPENED by any of
        # it: W385624 and W385625 are not implemented and their graphs are
        # untouched.
        self.assertEqual(fresh_attempt.fresh_attempt_rows(self.jobs), [])
        self.assertEqual(self.journal(episodes.CORRECT_KIND), [])
        self.assertEqual(
            failure_analysis.failure_of(self.jobs,
                                        self.only_key())["execution"]
            ["disposition"], "unable")

    def test_an_analysis_that_wrote_a_candidate_is_refused_by_the_tick(self):
        """The mutation attempt, refused on the production path too."""
        self.settled()
        self.tick()
        key = self.only_key()
        attempt_id = failure_analysis.analysis_attempt_id(key)
        # Replace the frozen result with one carrying a candidate output.
        self.control._connection.execute(
            "DELETE FROM outputs WHERE runtime_attempt_id = ?", (attempt_id,))
        self.control._connection.execute(
            "DELETE FROM output_artifacts WHERE runtime_attempt_id = ?",
            (attempt_id,))
        tree, content = self._custody_tree(attempt_id, "proposal", b"{}\n")
        self._frozen(
            attempt_id, disposition="completed",
            outputs=self.analysis_outputs(
                attempt_id,
                report=analysis_report(
                    key,
                    failure_analysis.intent_of(self.jobs,
                                               key)["input_digest"]))
            + [self._output(attempt_id, "proposal",
                            kind="git-change-proposal", content=content,
                            metadata={}, locator="file://" + tree)],
            participant=ANALYST, generation=9, result_id="result-mutating")
        report = self.tick(LATER)
        self.assertEqual(self.analysed(report),
                         [("deliver", "refused", "policy")])
        self.assertIsNone(failure_analysis.owner_item_of(self.jobs, key))


class NoRecursiveAnalysisIsReachableFromTheTick(ProductionCase):
    """Both exclusions, from the production entry point."""

    def test_the_analysis_attempt_has_no_settled_ending_to_observe(self):
        self.settled()
        self.driven()
        key = self.only_key()
        self.assertEqual(
            [one["attempt_id"]
             for one in failure_analysis.settled_trigger_endings(self.jobs)],
            [failure_analysis.failure_of(self.jobs,
                                         key)["selectors"]["attempt_id"]])
        self.assertNotIn(failure_analysis.analysis_attempt_id(key),
                         [one["attempt_id"] for one
                          in failure_analysis.settled_trigger_endings(
                              self.jobs)])
        self.assertEqual(len(self.journal(failure_analysis.FAILURE_KIND)), 1)

    def test_an_ending_by_the_declared_analyst_is_refused_by_the_tick(self):
        """The configuration half, reached through the real pass."""
        self.settled(participant=ANALYST)
        report = self.tick()
        self.assertEqual(self.analysed(report),
                         [("observe", "refused", "policy")])
        self.assertEqual(failure_analysis.failures_of(self.jobs), {})
        self.assertEqual(self.analyst.orders, [])


class TheDeploymentProducesTheDeclaredWorkerAndProfile(unittest.TestCase):
    """The producer, and what an operator may and may not say with it."""

    def test_it_fills_the_schema_role_profile_digest_and_outputs(self):
        held = failure_analysis.declared_analysis_worker(
            dict(DEPLOYMENT_DECLARED))
        self.assertEqual(held, {
            "schema": "baton.v12.recovery-analysis-worker/1",
            "role": "analysis",
            "worker_id": "analysis-worker-1",
            "participant": ANALYST,
            "principal": ANALYST_PRINCIPAL,
            "profile": "stage1-analysis/1",
            "profile_digest": "sha256:" + APPROVED_PROFILE_DIGEST,
            "permitted_outputs": ["analysis", "partial"],
            "capability_digest": "sha256:" + "c" * 64})
        # AND IT IS WHAT THE VALIDATOR ACCEPTS, which is the binding that
        # makes the producer usable at all.
        self.assertEqual(failure_analysis.check_analysis_declaration(held),
                         held)

    def test_the_owner_approved_profile_is_not_a_configurable_member(self):
        for extra in ("profile", "profile_digest", "permitted_outputs",
                      "schema", "role"):
            with self.assertRaises(ContractRefusal) as caught:
                failure_analysis.declared_analysis_worker(
                    dict(DEPLOYMENT_DECLARED, **{extra: "anything"}))
            self.assertIn("not configured", caught.exception.message)

    def test_a_missing_declared_fact_refuses_with_the_member_named(self):
        for name in failure_analysis.WORKER_DECLARED:
            held = dict(DEPLOYMENT_DECLARED)
            del held[name]
            with self.assertRaises(ContractRefusal) as caught:
                failure_analysis.declared_analysis_worker(held)
            self.assertIn(name, caught.exception.message)

    def test_the_produced_declaration_binds_the_role_to_no_provider(self):
        held = failure_analysis.declared_analysis_worker(
            dict(DEPLOYMENT_DECLARED))
        body = json.dumps(held)
        for forbidden in ("adapter", "image", "model", "provider", "claude",
                          "anthropic"):
            self.assertNotIn(forbidden, body.lower())

    def test_a_participant_that_is_its_own_principal_refuses(self):
        with self.assertRaises(ContractRefusal):
            failure_analysis.declared_analysis_worker(
                dict(DEPLOYMENT_DECLARED, principal=ANALYST))

    def test_the_four_declared_facts_are_the_operator_half(self):
        self.assertEqual(failure_analysis.WORKER_DECLARED,
                         ("worker_id", "participant", "principal",
                          "capability_digest"))
        self.assertEqual(sorted(DEPLOYMENT_DECLARED),
                         sorted(failure_analysis.WORKER_DECLARED))


class TheDerivedAnalysisIdentityIsStableAcrossEveryReEntry(
        unittest.TestCase):
    """Exact retry reuses the identity; it is never allocated."""

    def test_it_is_derived_from_the_failure_key_alone(self):
        key = "sha256:" + "1a" * 32
        self.assertEqual(failure_analysis.analysis_attempt_id(key),
                         "analysis-" + "1a" * 32)
        self.assertEqual(failure_analysis.analysis_attempt_id(key),
                         failure_analysis.analysis_attempt_id(key))

    def test_two_failures_never_share_an_analysis_identity(self):
        first = failure_analysis.analysis_attempt_id("sha256:" + "1" * 64)
        second = failure_analysis.analysis_attempt_id("sha256:" + "2" * 64)
        self.assertNotEqual(first, second)

    def test_a_value_that_is_not_a_failure_key_refuses(self):
        for bad in ("", "writer-attempt-1", "sha1:" + "a" * 40):
            with self.assertRaises(ContractRefusal):
                failure_analysis.analysis_attempt_id(bad)


class TheSeamContractIsOwnedBeforeAnythingIsSpent(ProductionCase):
    """`check_analysis_seam`, and the four members it names."""

    def test_the_closed_surface_is_written_down(self):
        self.assertEqual(failure_analysis.ANALYSIS_SEAM,
                         ("control", "declaration", "destination", "launch"))

    def test_every_member_is_required(self):
        for name in failure_analysis.ANALYSIS_SEAM:
            seam = Seam(self.control, self.declaration, OWNER, self.analyst)
            setattr(seam, name, None)
            held = self.refusal(failure_analysis.check_analysis_seam, seam)
            self.assertIn(name, held.message)
            self.assertEqual(held.code, "capability")

    def test_a_launch_that_cannot_be_called_refuses(self):
        seam = Seam(self.control, self.declaration, OWNER, "not-a-capability")
        self.assertIsNotNone(
            self.refusal(failure_analysis.check_analysis_seam, seam))

    def test_an_accepted_seam_answers_its_owned_members(self):
        seam = Seam(self.control, self.declaration, OWNER, self.analyst)
        held = failure_analysis.check_analysis_seam(seam)
        self.assertIs(held["control"], self.control)
        self.assertEqual(held["declaration"], self.declaration)
        self.assertEqual(held["destination"], OWNER)
        self.assertIs(held["launch"], self.analyst)


class TheAnalysisOwnAdmittedBoundIsWhatExpiresIt(ProductionCase):
    """The analysis clock, isolated from the original Job's own.

    THE JOB SELECTS NO FINITE CONTROL HERE, deliberately: with one, its own
    stage deadline runs 4800 seconds from the same instant and its fence is
    reached first -- which is correct behaviour and is covered above, and
    which makes it impossible to see the analysis's OWN bound decide. This
    case removes the other clock so that bound is the only one left.
    """

    CONTROL_PROFILE = None

    def test_an_analysis_that_never_landed_expires_on_its_own_bound(self):
        self.analyst.in_flight = 50
        self.settled()
        self.tick()
        key = self.only_key()
        intent = failure_analysis.intent_of(self.jobs, key)
        self.assertEqual(intent["deadlines"]["job_deadline_at"],
                         "2026-09-02T01:20:00.000Z")
        self.assertIsNone(cancellation.fence_of(self.jobs, "job-a"))
        self.assertEqual(self.analysed(self.tick(LATER)),
                         [("deliver", "held", "launched")])
        report = self.tick(AFTER_DEADLINE)
        self.assertEqual(self.analysed(report),
                         [("deliver", "delivered", "analysis-expired")])
        item = failure_analysis.owner_item_of(self.jobs, key)
        self.assertIn("4800-second", item["why"])
        self.assertIn("mid-turn", item["why"])
        self.assertEqual(item["partials"], [])
        # THE ORIGINAL JOB'S DEADLINES ARE NOT READ, MOVED OR EXTENDED by any
        # of this: the analysis admission has its own clock and this Job has
        # none at all.
        self.assertEqual(job_control.expiries_of(self.jobs), {})

    def test_a_lost_launch_holds_and_then_reports_unknown_cessation(self):
        """The fault cut "after possible launch with lost reply".

        NEVER READ AS "NOTHING WAS LAUNCHED", which is how a second provider
        turn happens. The dispatch intent names an attempt the control store
        cannot account for, so the pass HOLDS -- and what makes the hold
        finite is the owner-approved bound, not a retry: at the admitted
        deadline the owner gets ONE qualified item and no replacement is
        ordered.
        """
        self.analyst.lands = False
        self.settled()
        # One tick observes and dispatches; the dispatch intent stands and the
        # control store accounts for no attempt, so the next tick HOLDS.
        self.tick()
        self.assertEqual(self.analysed(self.tick(LATER)),
                         [("deliver", "held", "unknown")])
        # AND THE ADMITTED DEADLINE IS WHAT MAKES THE HOLD FINITE.
        report = self.tick(AFTER_DEADLINE)
        self.assertEqual(
            self.analysed(report),
            [("deliver", "delivered", "analysis-unknown-cessation")])
        item = failure_analysis.owner_item_of(self.jobs, self.only_key())
        self.assertEqual(item["partials"], [])
        self.assertIn("unknown", item["why"])
        # NO SECOND TURN WAS EVER ORDERED on any of those ticks.
        self.assertEqual(len(self.analyst.orders), 1)

class TheTickReportIsAClosedDocumentAndNotProse(ProductionCase):
    """What an operator watching the service is told, and its bounds."""

    def test_the_recovery_record_contract_is_closed(self):
        required, optional = documents.CONTRACTS["recovery.analysis"]
        self.assertEqual(required,
                         ("failure_key", "stage_id", "act", "outcome"))
        self.assertEqual(optional, ("detail",))
        with self.assertRaises(ContractRefusal):
            documents.recovery_analysis(
                failure_key=None, stage_id="s", act="observe",
                outcome="held", invented="no")
        with self.assertRaises(ContractRefusal):
            documents.recovery_analysis(stage_id="s", act="observe",
                                        outcome="held")

    def test_the_sweep_report_carries_analysed_only_when_it_acted(self):
        self.assertEqual(documents.CONTRACTS["sweep"][1],
                         ("analysed", "cancelled", "expired"))
        self.assertNotIn("analysed", self.tick())
        self.settled()
        self.assertIn("analysed", self.tick(LATER))

    def test_the_acts_and_outcomes_are_closed_vocabularies(self):
        self.assertEqual(failure_analysis.ANALYSIS_ACTS,
                         ("observe", "dispatch", "deliver"))
        self.assertEqual(failure_analysis.ANALYSIS_OUTCOMES,
                         ("observed", "dispatched", "delivered", "held",
                          "refused"))
        self.settled()
        for report in self.driven(instants=(NOW, LATER, AFTER_DEADLINE)):
            for one in report.get("analysed", []):
                self.assertIn(one["act"], failure_analysis.ANALYSIS_ACTS)
                self.assertIn(one["outcome"],
                              failure_analysis.ANALYSIS_OUTCOMES)

    def test_a_contained_refusal_travels_as_its_typed_pair_only(self):
        """Never a refusal's prose, which is composed from worker bytes."""
        failed = self.settled()
        self.repointed(failed, head="0" * 40)
        held = self.tick()["analysed"]
        self.assertEqual(len(held), 1)
        self.assertEqual(sorted(held[0]["detail"]), ["category", "code"])
        self.assertEqual(held[0]["detail"],
                         {"category": "ambiguous", "code": "collection"})

    def test_the_frozen_disposition_mapping_answers_for_the_whole_vocabulary(
            self):
        self.assertEqual(sorted(failure_analysis.ANALYSIS_ENDINGS),
                         sorted(failure_analysis.RESULT_DISPOSITIONS))
        self.assertIsNone(failure_analysis.ANALYSIS_ENDINGS["completed"])
        for word in ("unable", "plan-rejected", "cancelled"):
            self.assertIn(failure_analysis.ANALYSIS_ENDINGS[word],
                          failure_analysis.ENDPOINT_OUTCOMES)

    def test_the_trigger_stage_kind_is_the_producers(self):
        self.assertEqual(failure_analysis.TRIGGER_STAGE_KIND,
                         "implementation")
        self.assertIn(failure_analysis.TRIGGER_STAGE_KIND,
                      documents.STAGE_KINDS)


class TheAnalystReceivesTheFixedInputAndNothingElse(ProductionCase):
    """What the declared worker is actually delivered by the tick."""

    def test_the_delivered_document_is_the_immutable_analysis_input(self):
        failed = self.settled()
        self.tick()
        document = self.analyst.orders[0]
        key = self.only_key()
        self.assertEqual(document["failure_key"], key)
        self.assertEqual(
            document["input_digest"],
            failure_analysis.intent_of(self.jobs, key)["input_digest"])
        del failed

    def test_the_launch_is_given_the_admitted_intent_and_its_deadlines(self):
        self.settled()
        self.tick()
        order = self.analyst.orders[0]
        intent = failure_analysis.intent_of(self.jobs, self.only_key())
        self.assertEqual(order["participant"], intent["participant"])
        self.assertEqual(order["deadline"],
                         intent["deadlines"]["job_deadline_at"])
        self.assertEqual(order["job_id"], intent["job_id"])

    def test_no_turn_is_ordered_before_its_dispatch_intent_is_durable(self):
        """Intent before effect, proved by what the store held when asked."""
        seen = []

        def launch(*, attempt_id, document, intent):
            # THE RECORD MUST ALREADY BE THERE. A launch ordered before its
            # dispatch intent was committed is exactly the blind dispatch this
            # whole module is built to prevent.
            seen.append(failure_analysis.dispatch_of(
                self.jobs, document["failure_key"]))
            return self.analyst(attempt_id=attempt_id, document=document,
                                intent=intent)

        self.acts.recovery_analysis = Seam(self.control, self.declaration,
                                           OWNER, launch)
        self.settled()
        self.tick()
        self.assertEqual(len(seen), 1)
        self.assertIsNotNone(seen[0])
        self.assertEqual(seen[0]["analysis_attempt_id"],
                         failure_analysis.analysis_attempt_id(self.only_key()))


if __name__ == "__main__":   # pragma: no cover
    unittest.main()
