"""Selected W170385 managed apply and settlement evidence.

Git mutations in these cases are confined to disposable fixture repositories.
The local receipt cases are component evidence, not complete managed execution.
"""
import os
import tempfile
import unittest
import json
from pathlib import Path

from baton_v12.integration.git_profile import GitIntegrationProfile, IntegrationProfileRefusal
from tools.stage_execution import _git_run
from tests.tools.test_managed_preparation import RealLine


class AnOrdinaryManagedIntegration(unittest.TestCase):
    def test_failed_preparation_resumes_after_admission_is_closed(self):
        from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
        from baton_v12.job_manager import scheduler
        from baton_v12.contracts import ContractRefusal
        from unittest import mock
        case = OneManagedPreparationCompletes("run")
        self.addCleanup(case.doCleanups)
        release = scheduler.release
        cuts = []
        def interrupted(store, assignment, reason):
            if reason == "managed-integration-failed" and not cuts:
                cuts.append(True)
                raise ContractRefusal("refused", "precondition", "selected failure after closing root admission")
            return release(store, assignment, reason)
        with mock.patch.object(scheduler, "release", interrupted):
            case.complete(uncertain=True)
        self.assertEqual(len(cuts), 1)

    def test_preparation_judgments_apply_and_target_settle(self):
        self.complete()

    def test_reopen_after_target_effect_before_coordinator_settlement(self):
        self.complete(cut="target-effect")

    def test_a_failed_apply_is_collected_and_settles_without_a_target_effect(self):
        self.complete(failed=True)

    def test_reopen_after_retained_adoption(self):
        self.complete(cut="adoption")

    def test_reopen_after_derived_publication(self):
        self.complete(cut="publication")

    def test_unknown_target_effect_remains_a_visible_hold_after_reopen(self):
        self.complete(cut="unknown-effect")

    def test_original_job_limit_times_out_the_managed_apply(self):
        self.complete(failed=True, timed_out=True)

    def test_missing_independent_judgment_cannot_admit_apply(self):
        self.complete(denied="missing")

    def test_nonaccepting_independent_judgment_cannot_admit_apply(self):
        self.complete(denied="rejected")

    def test_changed_collection_mapping_cannot_admit_apply(self):
        self.complete(denied="mapping")

    def test_reopen_after_authority_receipt_before_final_handoff(self):
        self.complete(cut="authority-receipt")

    def test_reopen_after_failed_outcome_before_root_release(self):
        self.complete(cut="failed-outcome", failed=True)

    def test_a_grant_withdrawn_after_admission_prevents_start(self):
        self.complete(denied="grant")

    def test_target_drift_after_admission_prevents_start(self):
        self.complete(denied="target")

    def complete(self, cut=None, failed=False, timed_out=False, denied=None):
        import subprocess
        import sys
        import time
        from types import MethodType
        from tests.tools import test_stage_execution as stage_fixture
        from tests.tools.test_managed_preparation import OneManagedPreparationCompletes, WORKER
        from tests.job_manager import fixtures
        from baton_v12.job_manager import sweep
        from baton_v12.job_manager.integration_capacity import integration_capacity_of
        from baton_v12.integration import reconciliation

        case = OneManagedPreparationCompletes("run")
        self.addCleanup(case.doCleanups)

        def configure(world):
            if hasattr(world, "_managed_configuration"):
                return world._managed_configuration
            methods = stage_fixture.TwoBoundJobsTraverseServingAndCorrection
            world.JUDGMENT_WORKS = methods.JUDGMENT_WORKS
            for name in ("judgment_work", "judgment_execution", "judgment_task_bytes", "judgment_task_document", "judgment_workers", "judgment_turn"):
                setattr(world, name, MethodType(getattr(methods, name), world))
            world.manifest_over = MethodType(stage_fixture.EachJobBindsItsOwnDeploymentAndLine.manifest_over, world)
            world.vcs_in = MethodType(methods.vcs_in, world)
            world.deployment_of = lambda value: getattr(value, "composed", value).deployment
            world.quiescing = lambda: stage_fixture._ConcurrentEngine()
            if timed_out:
                from baton_v12.job_manager import documents
                world.submission["schema"] = documents.SUBMISSION_SCHEMA
                world.submission["jobs"][0]["execution_limits"] = {"verification_command_seconds": 1}
            target = os.path.join(world.root, "managed-target.git")
            self.assertEqual(_git_run(["git", "clone", "--quiet", "--bare", world.source, target])["returncode"], 0)
            world._managed_configuration = {"result_judgment_workers": world.judgment_workers("job-a"), "integration_target": target,
                    "integration_target_reference": "refs/heads/main", "schema": "baton.v12.stage-execution-deployment/2",
                    "job_bindings": [{"job_id": "job-a", "job_work_id": world.work, "review_work_id": world.work,
                                      "line_declared_base": world.base, "canonical_target_id": "target-1", "source_worker_id": "implementation-worker"}]}
            return world._managed_configuration

        def adopted(world, held, prepared):
            deployment = held.composed.deployment
            processes, logs, event_homes = [], [], []
            def cleanup():
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                for log in logs:
                    log.close()
            self.addCleanup(cleanup)
            original_engine = world.engine
            world.quiescing = lambda: original_engine
            starts = []
            def engine(argv, **options):
                answer = original_engine(argv, **options)
                if argv[1] != "run" or "--entrypoint" in argv:
                    if argv[1] in ("stop", "rm"):
                        for process in processes:
                            process.wait(timeout=5)
                    return answer
                mounts = {}
                for index, arg in enumerate(argv[:-1]):
                    if arg == "--mount":
                        parts = dict(part.split("=", 1) for part in argv[index + 1].split(",") if "=" in part)
                        mounts[parts["target"]] = parts["source"]
                if not os.path.isfile(os.path.join(mounts.get("/input/source", ""), "managed-apply.json")):
                    return answer
                capacity = integration_capacity_of(held.job, prepared["managed_result_id"])
                phases = {one["phase"]: one for one in capacity["members"]}
                self.assertEqual(phases["apply"]["state"], "admitted")
                self.assertEqual(phases["prepare"]["state"], "ended")
                self.assertNotIn(deployment.given["integration_target"], mounts.values())
                starts.append(phases["apply"]["execution_attempt_id"])
                event_homes.append(next(source for target, source in mounts.items() if target.endswith('/events')))
                code = r'''
import functools, json, sys
sys.path.insert(0, sys.argv[1])
import baton_worker, integration_entry
import traceback
original_work = integration_entry.ManagedApplyAgent.work
def traced_work(self, *args):
    try:
        return original_work(self, *args)
    except BaseException:
        traceback.print_exc()
        raise
integration_entry.ManagedApplyAgent.work = traced_work
original_handle = baton_worker.handle
def traced_handle(*args):
    try:
        return original_handle(*args)
    except BaseException:
        traceback.print_exc()
        raise
baton_worker.handle = traced_handle
mounts = json.loads(sys.argv[2])
baton_worker.INPUT_ROOT = mounts['/input']
baton_worker.OUTPUT_ROOT = mounts['/output']
integration_entry.ManagedApplyAgent = functools.partial(integration_entry.ManagedApplyAgent,
    output_root=mounts['/output'])
launch = next(source for target, source in mounts.items() if target.endswith('launch.json'))
command = next(source for target, source in mounts.items() if target.endswith('/command'))
event = next(source for target, source in mounts.items() if target.endswith('/events'))
sys.exit(integration_entry.main(launch_place=launch, command_root=command, event_root=event, bundle_root=mounts['/input/source'], scratch=sys.argv[3]))
'''
                log = tempfile.TemporaryFile()
                logs.append(log)
                processes.append(subprocess.Popen([sys.executable, "-c", code, str(WORKER), json.dumps(mounts),
                                                    os.path.join(world.root, "apply-scratch")], stdout=log, stderr=log))
                return answer
            # All these are the same configured fake engine boundary. The
            # apply process itself executes the real ordinary entry/workload.
            operations = deployment._integration_operations
            parent = operations.operations if hasattr(operations, "operations") else operations
            from baton_v12.worker_manager.oci import EnginePort
            parent._worker.engine = EnginePort(engine)
            deployment._engine_run = engine
            cuts, reopened, effects = [], [], []
            from unittest import mock
            from baton_v12.contracts import ContractRefusal
            original_effect = GitIntegrationProfile.publish_with_receipt
            def interrupted_effect(profile, *args, **kwargs):
                effects.append(True)
                answer = None if cut == "unknown-effect" else original_effect(profile, *args, **kwargs)
                if cut in ("target-effect", "unknown-effect") and not cuts:
                    cuts.append({"receipt": answer, "root": integration_capacity_of(held.job, prepared["managed_result_id"])["root"]["lifecycle"],
                                 "publication": reconciliation.publication_of(deployment.integration, prepared["managed_result_id"], "apply")["state"]})
                    raise ContractRefusal("refused", "precondition", "selected interruption after the atomic target effect")
                return answer
            effect_patch = mock.patch.object(GitIntegrationProfile, "publish_with_receipt", interrupted_effect)
            effect_patch.start()
            self.addCleanup(effect_patch.stop)
            if cut == "authority-receipt":
                imported = reconciliation.record_managed_imported
                def lost_final(*args, **kwargs):
                    if not cuts:
                        cuts.append({"root": "open", "publication": "settled"})
                        raise ContractRefusal("refused", "precondition", "selected loss after Authority receipt")
                    return imported(*args, **kwargs)
                final_patch = mock.patch.object(reconciliation, "record_managed_imported", lost_final)
                final_patch.start()
                self.addCleanup(final_patch.stop)
            if cut == "failed-outcome":
                from baton_v12.job_manager import integration_capacity
                ending = integration_capacity.begin_integration_ending
                def lost_failure(*args, **kwargs):
                    if kwargs["reason"] == "managed integration failed" and not cuts:
                        cuts.append({"root": "open", "publication": None})
                        raise ContractRefusal("refused", "precondition", "selected loss after owned failure")
                    return ending(*args, **kwargs)
                failure_patch = mock.patch.object(integration_capacity, "begin_integration_ending", lost_failure)
                failure_patch.start()
                self.addCleanup(failure_patch.stop)
            forbidden = []
            def host_git(argv, **kwargs):
                if not argv or argv[0] != "git" or "merge" in argv:
                    forbidden.append(list(argv))
                    raise AssertionError("managed coordinator attempted a merge or harness")
                return _git_run(argv, **kwargs)
            host_patch = mock.patch.object(stage_fixture.stage_execution, "_git_run", host_git)
            host_patch.start()
            self.addCleanup(host_patch.stop)
            for argv in (["python3", "harness.py"], ["git", "merge", "candidate"]):
                with self.assertRaises(AssertionError):
                    stage_fixture.stage_execution._git_run(argv)
            forbidden.clear()
            if denied == "mapping":
                from tools.integration_placement import ManagedAuthorization
                authorize = ManagedAuthorization.authorized
                def changed_mapping(owner, operands):
                    return authorize(owner, dict(operands, content_digest="sha256:" + "9" * 64))
                mapping_patch = mock.patch.object(ManagedAuthorization, "authorized", changed_mapping)
                mapping_patch.start()
                self.addCleanup(mapping_patch.stop)
            if denied in ("grant", "target"):
                from baton_v12.job_manager import integration_capacity
                from baton_v12.integration import queue
                admission = integration_capacity.admit_integration_execution
                withdrawn = []
                def after_admission(*args, **kwargs):
                    answer = admission(*args, **kwargs)
                    if kwargs["phase"] == "apply" and not withdrawn:
                        if denied == "grant":
                            queue.block_target(deployment.integration, **kwargs["grant"], reason="selected grant withdrawal", detail={"why": "pre-start gate test"})
                        else:
                            from baton_v12.contracts import digest
                            source = os.path.join(deployment.given["state_root"], "managed-results", digest(prepared["managed_result_id"])[7:], "objects")
                            self.assertEqual(_git_run(["git", "--git-dir=" + deployment.given["integration_target"], "fetch", "--quiet", source, prepared["derived_candidate"]["revision"]])["returncode"], 0)
                            self.assertEqual(_git_run(["git", "--git-dir=" + deployment.given["integration_target"], "update-ref", "refs/heads/main", prepared["derived_candidate"]["revision"], world.base])["returncode"], 0)
                        withdrawn.append(True)
                    return answer
                admission_patch = mock.patch.object(integration_capacity, "admit_integration_execution", after_admission)
                admission_patch.start()
                self.addCleanup(admission_patch.stop)
            judged, reports = set(), []
            def reopen():
                nonlocal deployment
                retired = held.composed
                old_authority = retired.deployment.authority
                retired.close()
                held.job.close()
                held.control.close()
                import sqlite3
                with self.assertRaises(sqlite3.ProgrammingError):
                    old_authority.project_work(world.work)
                held.job, held.control, held.composed = world.serving()
                world._composed = held.composed
                deployment = held.composed.deployment
                deployment._integration_operations._worker.engine = EnginePort(engine)
                deployment._engine_run = engine
                reopened.append(True)
            if cut == "adoption":
                reopen()
            for _ in range(10 if denied else 200):
                reports.append(sweep(held.job, held.composed, now=fixtures.NOW))
                if cuts and not reopened:
                    self.assertEqual(cuts[0]["root"], "open")
                    self.assertEqual(cuts[0]["publication"], {"authority-receipt": "settled", "failed-outcome": None}.get(cut, "intended"))
                    reopen()
                current = reconciliation.managed_result_of(deployment.integration, prepared["managed_result_id"])
                if cut == "publication" and current["state"] == "published" and not reopened:
                    reopen()
                for key, execution in deployment.judges.items():
                    if key not in judged:
                        if denied == "missing" and len(judged) == 2:
                            continue
                        world.judgment_turn(held, execution, verdict="changes-requested" if denied == "rejected" else "accepted")
                        judged.add(key)
                result = reconciliation.managed_result_of(deployment.integration, prepared["managed_result_id"])
                state = world.states(held.job, held.composed)["integration"]
                if state == "exceptional" or (state == "completed" and integration_capacity_of(held.job, result["managed_result_id"])["root"]["lifecycle"] == "ended"):
                    break
                time.sleep(0.01)
            for log in logs:
                log.seek(0)
            if cut == "target-effect" and state == "completed":
                receipt = deployment.authority.receipt(result["derived_proposal_id"], "integration")
                reopen()
                for _ in range(2):
                    sweep(held.job, held.composed, now=fixtures.NOW)
                self.assertEqual(world.states(held.job, held.composed)["integration"], "completed")
                self.assertEqual(deployment.authority.receipt(result["derived_proposal_id"], "integration"), receipt)
            diagnostics = {"reports": [one for one in reports if one.get("started") or one.get("spoken")][-4:],
                           "logs": [log.read().decode(errors="replace") for log in logs],
                           "events": [[(file.name, file.read_text()) for file in Path(home).glob("*.json")] for home in event_homes],
                           "apply": [(one.request, one.operations._worker.observed_exchange({"attempt_id": attempt})) for attempt, one in getattr(held.composed.integrator, "managed_runtimes", {}).items()]}
            from baton_v12.job_manager.projection import stage_states, gates_of
            self.assertEqual(forbidden, [])
            dependent = {"depends_on": json.dumps([{"job_id": "job-a", "kind": "integration"}])}
            gate = gates_of(dependent, stage_states(held.job, held.composed))[0]
            self.assertEqual(gate["open"], not failed and not denied and cut != "unknown-effect")
            if denied:
                self.assertNotEqual(state, "completed", diagnostics)
                self.assertEqual(starts, [])
                self.assertEqual(effects, [])
                self.assertIsNone(reconciliation.publication_of(deployment.integration, result["managed_result_id"], "apply"))
                self.assertEqual(integration_capacity_of(held.job, result["managed_result_id"])["root"]["lifecycle"], "open")
                self.assertEqual(deployment.reconciliation_profile.revision(deployment.given["integration_target"], "refs/heads/main"), prepared["derived_candidate"]["revision"] if denied == "target" else world.base)
                details = json.dumps(reports)
                self.assertIn({"missing": "frozen reports", "rejected": "did not accept", "mapping": "accepted frozen report", "grant": "grant", "target": "changed before the managed apply start"}[denied], details)
                return
            if cut == "unknown-effect":
                from baton_v12.integration import queue
                target = queue.target_of(deployment.integration, result["canonical_target_id"])
                self.assertEqual(state, "exceptional", diagnostics)
                self.assertEqual(target["state"], "blocked")
                self.assertIn("Human inspection", json.dumps(target))
                self.assertEqual(len(reopened), 1)
                self.assertEqual(len(effects), 1)
                self.assertEqual(len(starts), 1)
                self.assertEqual(queue.lease_of(deployment.integration, "managed-lease:" + starts[0])["state"], "live")
                self.assertEqual(integration_capacity_of(held.job, result["managed_result_id"])["root"]["lifecycle"], "open")
                self.assertEqual(deployment.reconciliation_profile.revision(deployment.given["integration_target"], "refs/heads/main"), world.base)
                return
            if failed:
                from baton_v12.job_manager.integration_capacity import failed_integration_of
                from baton_v12.integration import queue
                capacity = integration_capacity_of(held.job, prepared["managed_result_id"])
                root = capacity["root"]
                self.assertEqual(world.states(held.job, held.composed)["integration"], "exceptional", diagnostics)
                failure = failed_integration_of(held.job, root["stage_id"], root["episode"])
                self.assertIsNotNone(failure, diagnostics)
                self.assertTrue(failure["settled"])
                self.assertEqual(root["lifecycle"], "ended")
                self.assertEqual(len(reopened), 1 if cut else 0)
                self.assertEqual(effects, [])
                self.assertEqual(len(starts), 1)
                measured = result["phases"]["apply"]["result"]["report"]["status"]
                self.assertIn(measured, (143, 137)) if timed_out else self.assertEqual(measured, 7)
                if timed_out:
                    self.assertEqual(result["phases"]["apply"]["task"]["execution_limits"]["boundaries"]["host_verification"]["seconds"], 1)
                self.assertEqual(deployment.reconciliation_profile.revision(deployment.given["integration_target"], "refs/heads/main"), world.base)
                self.assertEqual(deployment.authority.canonical_target(), world.base)
                self.assertIsNone(deployment.authority.receipt(result["derived_proposal_id"], "integration"))
                self.assertEqual(queue.lease_of(deployment.integration, "managed-lease:" + starts[0])["state"], "released")
                for _ in range(2):
                    sweep(held.job, held.composed, now=fixtures.NOW)
                self.assertEqual(len(starts), 1)
                self.assertEqual(world.states(held.job, held.composed)["integration"], "exceptional")
                return
            self.assertEqual(world.states(held.job, held.composed)["integration"], "completed", diagnostics)
            self.assertEqual(result["state"], "imported")
            self.assertEqual(len(reopened), 0 if cut is None else (2 if cut == "target-effect" else 1))
            self.assertEqual(len(judged), 3)
            self.assertEqual(len(starts), 1)
            self.assertEqual(len(effects), 1)
            self.assertEqual(len(processes), 1)
            self.assertEqual(processes[0].wait(timeout=5), 0)
            self.assertEqual(deployment.reconciliation_profile.revision(deployment.given["integration_target"], "refs/heads/main"), result["prepared"]["head"])
            self.assertEqual(deployment.authority.canonical_target(), result["prepared"]["head"])
            actual = _git_run(["git", "--git-dir=" + deployment.given["integration_target"], "show", "refs/heads/main:harness.py"])
            self.assertEqual(actual["returncode"], 0)
            self.assertEqual(actual["stdout"], "print('the corrected harness')\n")
            self.assertEqual(integration_capacity_of(held.job, result["managed_result_id"])["root"]["lifecycle"], "ended")
            print(json.dumps({"proof": "ordinary-managed-integration", "judgments": len(judged), "apply_starts": len(starts),
                              "result": result["managed_result_id"], "state": result["state"]}, sort_keys=True))

        body = "import pathlib, sys\nsys.exit(7 if 'apply-scratch' in str(pathlib.Path.cwd()) else 0)\n" if failed else None
        if timed_out:
            body = "import pathlib, time\nif 'apply-scratch' in str(pathlib.Path.cwd()): time.sleep(30)\n"
        case.complete(configured=configure, completed=adopted, base_harness=body)


class ThePreparationHandoffRetainsItsGitObjects(unittest.TestCase):
    def test_parent_publishes_retained_candidate_and_waits_for_real_receipts(self):
        from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
        from tests.job_manager import fixtures
        from baton_v12.job_manager import sweep
        from baton_v12.integration import reconciliation

        case = OneManagedPreparationCompletes("run")
        self.addCleanup(case.doCleanups)

        def configure(world):
            target = os.path.join(world.root, "publication-target.git")
            self.assertEqual(_git_run(["git", "clone", "--quiet", "--bare", world.source, target])["returncode"], 0)
            return {"integration_target": target, "integration_target_reference": "refs/heads/main"}

        def adopted(world, held, prepared):
            result_id = prepared["managed_result_id"]
            reports = []
            for _ in range(6):
                reports.append(sweep(held.job, held.composed, now=fixtures.NOW))
                result = reconciliation.managed_result_of(held.composed.deployment.integration, result_id)
                if result["state"] == "published":
                    break
            self.assertEqual(result["state"], "published", reports)
            self.assertEqual(reconciliation.retained_managed_preparation(held.composed.deployment.integration, result_id), prepared)
            authority = held.composed.deployment.authority
            proposal = authority.proposal(result["derived_proposal_id"])
            self.assertEqual(proposal["candidate_digest"], prepared["derived_candidate"]["revision"])
            self.assertEqual(proposal["assignment_ref"]["participant"], prepared["assignment"]["participant"])
            self.assertNotEqual(proposal["assignment_ref"], prepared["assignment"])
            for kind in ("verification", "review", "approval"):
                self.assertIsNone(authority.receipt(result["derived_proposal_id"], kind))
            print(json.dumps({"proof": "managed-publication-awaits-independent-receipts", "result": result_id,
                              "proposal": result["derived_proposal_id"], "state": result["state"]}, sort_keys=True))

        case.complete(completed=adopted, configured=configure)

    def test_ordinary_retained_custody_materializes_without_execution_roots(self):
        from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
        from tools.integration_placement import materialize_prepared_objects

        case = OneManagedPreparationCompletes("run")
        self.addCleanup(case.doCleanups)

        def adopted(world, held, prepared):
            self.assertIsNotNone(prepared["objects"])
            repository = os.path.join(world.root, "retained-derived-objects")
            answer = materialize_prepared_objects(held.control, prepared, repository=repository,
                                                   profile=GitIntegrationProfile(_git_run), reader=held.composed.deployment.integration_object_runner)
            self.assertEqual(answer["head"], prepared["derived_candidate"]["revision"])
            self.assertEqual(answer["tree"], prepared["derived_candidate"]["tree"])
            self.assertEqual(materialize_prepared_objects(held.control, prepared, repository=repository,
                                                          profile=GitIntegrationProfile(_git_run), reader=held.composed.deployment.integration_object_runner), answer)

        case.complete(completed=adopted)

    def test_exact_objects_and_git_modes_survive_the_preparation_scratch(self):
        """Real producer/workload export; ordinary retained custody is separate."""
        from tests.tools.test_managed_preparation import OnePreparationRunsThroughTheOrdinaryWorker

        class ExecutableCandidate(OnePreparationRunsThroughTheOrdinaryWorker):
            def history(self, conflicting=False):
                revisions = super().history(conflicting)
                self.line.run(["checkout", "--quiet", "-b", "executable-candidate", revisions["candidate"]])
                self.line.write("tool.sh", "#!/bin/sh\nexit 0\n")
                os.chmod(os.path.join(self.line.place, "tool.sh"), 0o755)
                revisions["candidate"] = self.line.commit("candidate includes an executable")
                return revisions

        case = ExecutableCandidate("run")
        self.addCleanup(case.doCleanups)
        case.setUp()
        answer = case.agent().work(case.launch(), case.declared())
        self.assertEqual(answer["disposition"], "completed")
        report = case.report()
        derived = report["derived_candidate"]
        objects = os.path.join(case.scratch, "objects")
        tree_entry = _git_run(["git", "-C", objects, "ls-tree", derived["revision"], "--", "tool.sh"])
        self.assertEqual(tree_entry["returncode"], 0)
        self.assertTrue(tree_entry["stdout"].startswith("100755 blob "))
        emitted = Path(case.output, "candidate", "tool.sh")
        self.assertEqual(emitted.read_bytes(), b"#!/bin/sh\nexit 0\n")
        self.assertEqual(emitted.stat().st_mode & 0o111, 0)
        self.assertTrue(Path(case.output, "objects", "objects.bundle").is_file())
        measured = next(one for one in report["states"]["combined"]["content"]["entries"] if one["path"] == "tool.sh")
        self.assertEqual(set(measured), {"path", "content_digest", "bytes"})
        portable = os.path.join(case.root.name, "input-objects-only")
        self.assertEqual(_git_run(["git", "init", "--quiet", "--bare", portable])["returncode"], 0)
        fetched = _git_run(["git", "-C", portable, "fetch", "--quiet", os.path.join(case.input, "source", "objects.bundle"), "refs/*:refs/input/*"])
        self.assertEqual(fetched["returncode"], 0)
        missing = _git_run(["git", "-C", portable, "cat-file", "-e", derived["revision"] + "^{commit}"])
        self.assertNotEqual(missing["returncode"], 0)
        retained = tempfile.TemporaryDirectory(prefix="v12-prepared-object-reader-")
        self.addCleanup(retained.cleanup)
        self.assertEqual(_git_run(["git", "init", "--quiet", "--bare", retained.name])["returncode"], 0)
        imported = _git_run(["git", "-C", retained.name, "fetch", "--quiet", str(Path(case.output, "objects", "objects.bundle")), "refs/baton/prepared/candidate:refs/retained/candidate"])
        self.assertEqual(imported["returncode"], 0)
        case.doCleanups()
        self.assertFalse(Path(case.scratch).exists())
        self.assertEqual(_git_run(["git", "-C", retained.name, "rev-parse", "refs/retained/candidate"])["stdout"].strip(), derived["revision"])
        self.assertEqual(_git_run(["git", "-C", retained.name, "rev-parse", "refs/retained/candidate^{tree}"])["stdout"].strip(), derived["tree"])
        mode = _git_run(["git", "-C", retained.name, "ls-tree", derived["revision"], "--", "tool.sh"])
        self.assertTrue(mode["stdout"].startswith("100755 blob "))
        print(json.dumps({"proof": "exact-preparation-object-export", "derived_revision": derived["revision"],
                          "derived_tree": derived["tree"], "git_mode": "100755", "scratch_gone": True}, sort_keys=True))


class TheTargetEffectAndReceiptAreOneTransaction(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory(prefix="v12-managed-apply-")
        self.addCleanup(self.home.cleanup)
        self.line = RealLine(os.path.join(self.home.name, "target"))
        self.line.write("feature.py", "VALUE = 1\n")
        self.old = self.line.commit("base")
        self.line.write("feature.py", "VALUE = 2\n")
        self.new = self.line.commit("approved")
        self.reference = "refs/baton/targets/local"
        self.line.run(["update-ref", self.reference, self.old])
        self.profile = GitIntegrationProfile(_git_run)
        self.receipt = {"publication": "publication-a", "old": self.old, "new": self.new}
        self.checks = []

    def publish(self, **changed):
        operands = dict(reference=self.reference, imported=self.new, reviewed=self.old,
                        publication_id="publication-a", receipt=self.receipt,
                        before_commit=lambda: self.checks.append("grant"))
        operands.update(changed)
        return self.profile.publish_with_receipt(self.line.place, **operands)

    def test_target_and_exact_receipt_survive_a_new_owner(self):
        before = self.profile.publication_receipt(self.line.place, publication_id="publication-a")
        self.assertIsNone(before)
        receipt = self.publish()
        self.assertEqual(self.checks, ["grant"])
        self.assertEqual(self.line.run(["show", self.reference + ":feature.py"]), "VALUE = 2")
        reopened = GitIntegrationProfile(_git_run)
        self.assertEqual(reopened.publication_receipt(self.line.place, publication_id="publication-a"), receipt)
        self.assertEqual(receipt["document"], self.receipt)

    def test_stale_target_cas_creates_no_receipt(self):
        self.line.run(["update-ref", self.reference, self.new, self.old])
        with self.assertRaises(IntegrationProfileRefusal):
            self.publish()
        self.assertEqual(self.profile.revision(self.line.place, self.reference), self.new)
        self.assertIsNone(self.profile.publication_receipt(self.line.place, publication_id="publication-a"))


    def test_receipt_collision_does_not_advance_the_target(self):
        reference = self.profile.publication_reference("publication-a")
        self.line.run(["update-ref", reference, self.old])
        with self.assertRaises(IntegrationProfileRefusal):
            self.publish()
        self.assertEqual(self.profile.revision(self.line.place, self.reference), self.old)
        self.assertEqual(self.line.run(["rev-parse", reference]), self.old)

    def test_lost_transaction_reply_recovers_without_another_effect(self):
        calls = []

        def lost(argv, **options):
            answer = _git_run(argv, **options)
            if "update-ref" in argv and "--stdin" in argv:
                calls.append(tuple(argv))
                raise RuntimeError("reply lost after transaction")
            return answer

        self.profile = GitIntegrationProfile(lost)
        with self.assertRaisesRegex(RuntimeError, "reply lost"):
            self.publish()
        recovered = GitIntegrationProfile(_git_run).publication_receipt(self.line.place, publication_id="publication-a")
        self.assertEqual(recovered["document"], self.receipt)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.profile.revision(self.line.place, self.reference), self.new)

    def test_grant_is_checked_after_receipt_object_work_before_transaction(self):
        seen = []

        def run(argv, **options):
            seen.append(tuple(argv))
            return _git_run(argv, **options)

        def revoked():
            self.assertTrue(any("hash-object" in argv for argv in seen))
            self.assertFalse(any("update-ref" in argv for argv in seen))
            raise RuntimeError("grant revoked")

        self.profile = GitIntegrationProfile(run)
        with self.assertRaisesRegex(RuntimeError, "grant revoked"):
            self.publish(before_commit=revoked)
        self.assertEqual(self.profile.revision(self.line.place, self.reference), self.old)
        self.assertIsNone(self.profile.publication_receipt(self.line.place, publication_id="publication-a"))


class TheLocalReceiptOwnerComposesWithPlacement(unittest.TestCase):
    """Real target receipt; surrounding authorization/exclusion remain fixtures."""

    def setUp(self):
        from tests.tools.test_managed_integration import PlacementCase
        self.case = PlacementCase("run")
        self.addCleanup(self.case.doCleanups)
        self.case.setUp()
        self.case.custody()
        self.case.stopped()
        self.configure(_git_run)

    def configure(self, runner):
        from integration_placement import LocalGitTargetOwner
        from tests.tools.test_managed_integration import ORCHESTRATION
        case = self.case
        case.profile = GitIntegrationProfile(runner)
        case.target_owner = LocalGitTargetOwner(
            coordinator=case.coordinator, manager=case.store, profile=case.profile,
            execution_owner=case.execution_owner, authorization=case.authorization,
            repository=case.repository, reference=case.reference, managed_result_id=ORCHESTRATION)

    def test_real_receipt_publication_and_historical_replay(self):
        first = self.case.publish()
        self.assertEqual(first["outcome"], "published")
        self.assertEqual(self.case.standing(), self.case.candidate)
        self.configure(_git_run)
        replayed = self.case.publish()
        self.assertEqual(replayed["outcome"], "replayed")
        self.assertEqual(replayed["imported_revision"], first["imported_revision"])

    def test_lost_reply_is_settled_from_the_real_receipt(self):
        calls = []

        def lost(argv, **options):
            answer = _git_run(argv, **options)
            if "update-ref" in argv and "--stdin" in argv:
                calls.append(tuple(argv))
                raise RuntimeError("target reply lost")
            return answer

        self.configure(lost)
        with self.assertRaisesRegex(RuntimeError, "target reply lost"):
            self.case.publish()
        self.configure(_git_run)
        self.assertEqual(self.case.publish()["outcome"], "resumed")
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.case.standing(), self.case.candidate)
