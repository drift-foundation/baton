"""C1/C2 proofs: deterministic provider children and a simulated OCI engine."""
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest

from tests.tools import correction_restart_trace as proof


def artifact(*, counted_reopen=False):
    world = proof.World()
    try:
        world.setUp()
        return world.run_scenario(counted_reopen=counted_reopen)
    finally:
        world.doCleanups()


def export(document):
    if os.environ.get("BATON_C_EVIDENCE"):
        Path(os.environ["BATON_C_EVIDENCE"]).write_text(json.dumps(document, indent=2) + "\n")


class UsefulCorrection(unittest.TestCase):
    def test_useful_correction_reaches_managed_target(self):
        observed = artifact()
        export(observed)
        self.assertEqual(proof.validate(observed), [])

    def test_preparation_fault_reports_terminal_before_fixture_cleanup(self):
        from unittest import mock
        injected = proof.MANAGED_CHILD.replace("reconciliation_entry.PreparationAgent=functools.partial(",
            "def fail_work(self, seen, declared): raise RuntimeError('selected preparation fault')\n    reconciliation_entry.PreparationAgent.work=fail_work\n    reconciliation_entry.PreparationAgent=functools.partial(")
        self.assertNotEqual(injected, proof.MANAGED_CHILD)
        with mock.patch.object(proof, "MANAGED_CHILD", injected):
            with self.assertRaises(AssertionError) as caught:
                artifact()
        self.assertTrue(str(caught.exception).startswith("{"), str(caught.exception))
        observed = json.loads(str(caught.exception))
        self.assertEqual(observed["failure"], "preparation did not answer")
        self.assertLess(observed["tick"], 100)
        self.assertEqual(len(observed["preparation"]), 1)
        exchange = next(iter(observed["preparation"].values()))
        self.assertIsNotNone(exchange["receipt"])
        self.assertEqual(exchange["terminal"]["ending"], "faulted")
        self.assertTrue(observed["children"])

    def test_unchanged_predecessor_artifacts_still_validate_without_execution(self):
        root = Path(__file__).resolve().parents[4]
        predecessor = root / "work/records/2026/09/finding-v12-deterministic-scheduler-stress/trace-160959-composed.json"
        body = predecessor.read_bytes()
        self.assertEqual(hashlib.sha256(body).hexdigest(), "5a3ead46c46b5586cbd3a74d7454b402fd04dfbe34414e33a061ac9e90fb9303")
        schedules = json.loads(body)["schedules"]
        self.assertEqual(len(schedules), 18)
        for schedule in schedules:
            self.assertEqual(proof.scheduler_trace.validate(schedule["artifact"]), [])


class TransactionBoundaryThroughTheConnectedPath(unittest.TestCase):
    """W236087: no external read inside a ControlStore transaction, measured CONNECTED.

    `tests/manager/test_provider_context.py` holds the admission boundary on a
    disposable fixture. This holds the SAME rule over the whole scenario the correction
    trace already drives -- open, save, exact stop, changes-requested correction, restore
    -- which is where `bind_context_invocation` and `revalidate_context_start` actually
    run. `PREPARATION-307667.md` directs reuse of this vehicle rather than a new one.

    THE OBSERVATION IS THE RESEARCH PROBE, generalised: wrap `ControlStore.transact`'s
    action to count depth, wrap the readers that are NOT this store's -- the filesystem
    walk, the Job-store attempt lookup, the attempt assignment and the Authority reader --
    and require that none of them is entered while the depth is non-zero.
    """

    def test_no_external_reader_runs_inside_a_control_transaction(self):
        import contextlib
        from unittest import mock

        from baton_v12.worker_manager import attempts, context_delivery, store
        from baton_v12.worker_manager import provider_context as context

        seen = []
        depth = [0]
        original_transact = store.ControlStore.transact

        def transact(this, operation_id, kind, signature, action):
            def counted(connection):
                depth[0] += 1
                try:
                    return action(connection)
                finally:
                    depth[0] -= 1
            return original_transact(this, operation_id, kind, signature, counted)

        def watching(name, original):
            def wrapper(*arguments, **keywords):
                if depth[0]:
                    seen.append(name)
                return original(*arguments, **keywords)
            return wrapper

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(store.ControlStore, "transact",
                                                  transact))
            stack.enter_context(mock.patch.object(
                context_delivery, "_open_absolute",
                watching("_open_absolute", context_delivery._open_absolute)))
            stack.enter_context(mock.patch.object(
                context, "_job_attempt",
                watching("_job_attempt", context._job_attempt)))
            stack.enter_context(mock.patch.object(
                attempts, "assignment_of",
                watching("attempts.assignment_of", attempts.assignment_of)))
            observed = artifact()

        # THE SCENARIO REALLY RAN, so an empty observation is not an empty run.
        self.assertEqual(proof.validate(observed), [])
        self.assertEqual(sorted(set(seen)), [], sorted(set(seen)))


class UsefulCorrectionInvalidEvidence(unittest.TestCase):
    """Every mutation is a synthetic invalid copy, never an owner receipt."""

    @classmethod
    def setUpClass(cls):
        cls.observed = artifact()
        cls().assertEqual(proof.validate(cls.observed), [])
        cls.rejections = []

    @classmethod
    def tearDownClass(cls):
        export({"kind": "C1 synthetic invalid-evidence results", "valid_observation": cls.observed, "rejections": cls.rejections})

    def rejects(self, name, mutate, expected):
        invalid = copy.deepcopy(self.observed)
        invalid["synthetic_invalid_evidence"] = name
        mutate(invalid)
        failures = proof.validate(invalid)
        self.assertIn(expected, {one["code"] for one in failures}, failures)
        self.rejections.append({"kind": "synthetic invalid evidence", "case": name, "expected": expected, "violations": failures})
        self.assertEqual(proof.validate(self.observed), [])

    def test_a_RUNNING_predecessor_is_rejected(self):
        """W236087 review 2026-09-29T20-25-55Z R1, the reviewer's own counterexample.

        The oracle bound no runtime identity, so changing BOTH runtime observations to
        `running` passed the whole counted validator. A restore riding a predecessor that is
        still executing is exactly what this proof must not admit, so it is now a refusal.
        """
        mutated = copy.deepcopy(self.observed)
        for name in ("initial", "revised"):
            mutated[name]["runtime"]["execution_runtime"] = "running"
        self.assertEqual([one["code"] for one in proof.validate(mutated)],
                         ["C1-runtime-destroyed", "C1-runtime-destroyed"])

    def test_a_REUSED_runtime_id_on_the_restored_use_is_rejected(self):
        """The other half of R1: one RUNTIME per execution.

        A restored use reporting the PREDECESSOR's runtime id would be naming an execution
        that is not its own, and the oracle could not see it. This is identity
        distinctness; the governed token's return ordering is still owed, and
        `correction_restart_trace.validate` says where that evidence lives.
        """
        mutated = copy.deepcopy(self.observed)
        mutated["revised"]["runtime"]["runtime_id"] = \
            mutated["initial"]["runtime"]["runtime_id"]
        self.assertIn("C1-runtime-distinct",
                      [one["code"] for one in proof.validate(mutated)])

    def opening_attempt(self):
        return self.observed["initial"]["settlement"]["attempt_id"]

    def restored_attempt(self):
        return self.observed["revised"]["settlement"]["attempt_id"]

    def restored_boundary(self, held):
        return [one for one in held["tokens"]["boundaries"]
                if one.get("execution") == self.restored_attempt()][0]

    def test_an_UNRETURNED_opening_token_at_the_restored_activation_is_rejected(self):
        """The ORDERING, mutated on the OPENING EXECUTION ALONE.

        W236087 review 2026-09-29T20-49-45Z: my first negative changed every generation-1
        observation, and the oracle keyed on generation alone -- so it passed for the wrong
        reason, and mutating only the opening execution still validated because another
        resource's generation 1 masked it. This mutates that one execution's observation and
        leaves any foreign generation 1 intact, which is what the tuple match now catches.
        """
        mutated = copy.deepcopy(self.observed)
        for one in self.restored_boundary(mutated)["observed"]:
            if one.get("execution") == self.opening_attempt():
                one["state"]["returned"] = False
        self.assertEqual([one["code"] for one in proof.validate(mutated)],
                         ["C1-token-returned-before-activation"])

    def test_an_ALREADY_ACTIVATED_new_token_is_rejected(self):
        """The other side of the boundary: the restored token is not yet activated there."""
        mutated = copy.deepcopy(self.observed)
        for one in self.restored_boundary(mutated)["observed"]:
            if one.get("execution") == self.restored_attempt():
                one["state"]["activation_started"] = "2026-09-02T00:00:00.000Z"
        self.assertIn("C1-token-new-not-activated",
                      [one["code"] for one in proof.validate(mutated)])

    def test_a_STALE_token_generation_on_the_restored_use_is_rejected(self):
        """A restored reservation reusing the opening generation is not a new token."""
        mutated = copy.deepcopy(self.observed)
        opening = [one for one in mutated["tokens"]["reservations"]
                   if one["execution"] == self.opening_attempt()][0]
        restored = [one for one in mutated["tokens"]["reservations"]
                    if one["execution"] == self.restored_attempt()][0]
        restored["generation"] = opening["generation"]
        restored["operation"] = opening["operation"]
        self.assertIn("C1-token-distinct",
                      [one["code"] for one in proof.validate(mutated)])

    def test_a_WRONG_token_CONTAINER_is_rejected(self):
        """Review R2 of 20-49-45Z: the exported container was ignored, so any value passed.

        `state.container` must be the execution's OWN runtime, and the boundary's container
        must be the restored execution's.
        """
        mutated = copy.deepcopy(self.observed)
        for one in self.restored_boundary(mutated)["observed"]:
            one["state"]["container"] = "runtime-somebody-else"
        self.assertEqual(sorted(set(one["code"] for one in proof.validate(mutated))),
                         ["C1-token-container"])
        moved = copy.deepcopy(self.observed)
        for one in moved["tokens"]["boundaries"]:
            one["container"] = "runtime-not-ours"
        self.assertIn("C1-token-boundary-container",
                      [one["code"] for one in proof.validate(moved)])

    def test_a_WRONG_token_LAUNCH_operation_is_rejected(self):
        """`state.launch` must be the operation the acquisition answered."""
        mutated = copy.deepcopy(self.observed)
        for one in self.restored_boundary(mutated)["observed"]:
            one["state"]["launch"] = "runtime.start:" + "0" * 64
        self.assertEqual(sorted(set(one["code"] for one in proof.validate(mutated))),
                         ["C1-token-launch"])

    def test_a_MISSING_or_DUPLICATED_token_observation_is_rejected(self):
        """Absence and a repeated tuple are both refusals, not silent passes."""
        absent = copy.deepcopy(self.observed)
        boundary = self.restored_boundary(absent)
        boundary["observed"] = [one for one in boundary["observed"]
                                if one.get("execution") != self.opening_attempt()]
        self.assertIn("C1-token-observation-missing",
                      [one["code"] for one in proof.validate(absent)])
        doubled = copy.deepcopy(self.observed)
        boundary = self.restored_boundary(doubled)
        boundary["observed"] = boundary["observed"] + [copy.deepcopy(boundary["observed"][0])]
        self.assertIn("C1-token-observation-conflict",
                      [one["code"] for one in proof.validate(doubled)])

    def test_identical_revised_code_is_rejected(self):
        self.rejects("revised code replaced by original", lambda x: x["revised"]["content"].__setitem__("scale.py", copy.deepcopy(x["initial"]["content"]["scale.py"])), "C1-code-unchanged")

    def test_unexecuted_or_wrong_byte_verifier_is_rejected(self):
        self.rejects("verifier never executed", lambda x: x["verifications"][1].__setitem__("execution", "not-run"), "C1-verifier-execution")
        self.rejects("verifier measures original bytes", lambda x: x["verifications"][1].__setitem__("code_digest", x["initial"]["content"]["scale.py"]["digest"]), "C1-verifier-bytes")
        self.rejects("revised verifier absent", lambda x: x["verifications"].pop(), "C1-verifier-missing")

    def test_target_receipt_naming_original_is_rejected(self):
        self.rejects("target receipt names original revision", lambda x: x["target"]["receipt"].__setitem__("candidate_digest", x["initial"]["checkpoint"]["head_object"]), "C1-target-receipt")
        self.rejects("target content names original code", lambda x: x["target"].__setitem__("code_digest", x["initial"]["content"]["scale.py"]["digest"]), "C1-target-bytes")

    def test_missing_or_forged_changes_requested_verdict_is_rejected(self):
        self.rejects("changes-requested verdict absent", lambda x: x.__setitem__("verdict", None), "C1-incomplete-evidence")
        self.rejects("changes-requested verdict forged", lambda x: x["verdict"].__setitem__("disposition", "accepted"), "C1-verdict")
        self.rejects("verdict names another checkpoint", lambda x: x["verdict"].__setitem__("checkpoint_id", x["revised"]["checkpoint"]["checkpoint_id"]), "C1-verdict-attribution")
        self.rejects("correction names original attempt", lambda x: x["correction"]["evidence"].__setitem__("routed", x["initial"]["settlement"]["attempt_id"]), "C1-correction-route")

    def test_reviewer_context_or_writable_line_access_is_rejected(self):
        self.rejects("reviewer receives producer context", lambda x: x["reviews"][0]["launch"].__setitem__("provider_context", x["initial"]["binding"]), "C1-review-context")
        def writable(x):
            source = next(m for m in x["reviews"][0]["mounts"] if m["target"] == "/input/source")
            source["source"] = x["reviews"][0]["producer_workspace"]
            source["readonly"] = False
        self.rejects("reviewer receives writable producer line", writable, "C1-review-writable-line")
        self.rejects("reviewer receives private mount", lambda x: x["reviews"][0]["mounts"].append({"source": x["reviews"][0]["private_context_root"], "target": "/run/baton/context", "readonly": True}), "C1-review-context")


class CountedReopen(unittest.TestCase):
    def test_manager_recomposition_preserves_both_positive_counts(self):
        observed = artifact(counted_reopen=True)
        export(observed)
        self.assertEqual(proof.validate(observed, counted_reopen=True), [])

    test_unchanged_predecessor_artifacts_still_validate_without_execution = UsefulCorrection.test_unchanged_predecessor_artifacts_still_validate_without_execution


class CountedReopenInvalidEvidence(unittest.TestCase):
    """Separate mutations of actual provider and engine observations."""

    @classmethod
    def setUpClass(cls):
        cls.observed = artifact(counted_reopen=True)
        cls().assertEqual(proof.validate(cls.observed, counted_reopen=True), [])
        cls.rejections = []

    @classmethod
    def tearDownClass(cls):
        export({"kind": "C2 synthetic invalid-evidence results", "valid_observation": cls.observed, "rejections": cls.rejections})

    def rejects(self, name, mutate, expected):
        invalid = copy.deepcopy(self.observed)
        invalid["synthetic_invalid_evidence"] = name
        mutate(invalid)
        failures = proof.validate(invalid, counted_reopen=True)
        self.assertIn(expected, {one["code"] for one in failures}, failures)
        self.rejections.append({"kind": "synthetic invalid evidence", "case": name, "expected": expected, "violations": failures})
        self.assertEqual(proof.validate(self.observed, counted_reopen=True), [])

    def duplicate(self, stream, point, revised=False):
        def mutate(x):
            counters = x["final_counters"] if point == "final" else x["reopen"][point]
            attempt = x["revised" if revised else "initial"]["binding"]["attempt_id"]
            counters[stream].append(copy.deepcopy(next(one for one in counters[stream] if one["attempt_id"] == attempt)))
        self.rejects(stream + " duplicate at " + point + (" revised use" if revised else " old use"), mutate, "C2-" + stream + ("-new-use" if revised else "-duplicate"))

    def test_duplicate_provider_is_rejected_independently(self):
        self.duplicate("provider", "after")
        self.duplicate("provider", "final")
        self.duplicate("provider", "final", revised=True)

    def test_duplicate_engine_is_rejected_independently(self):
        self.duplicate("engine", "after")
        self.duplicate("engine", "final")
        self.duplicate("engine", "final", revised=True)

    def test_missing_positive_baseline_is_rejected(self):
        for stream in ("provider", "engine"):
            self.rejects("missing " + stream + " baseline", lambda x, stream=stream: x["reopen"]["before"].__setitem__(stream, []), "C2-positive-baseline")

    def test_absent_actual_reopen_is_rejected(self):
        self.rejects("boundary deleted", lambda x: x.pop("reopen"), "C2-incomplete-evidence")
        self.rejects("no close or recompose performed", lambda x: x["reopen"].__setitem__("performed", False), "C2-reopen")

    def test_changed_verdict_checkpoint_or_attempt_is_rejected(self):
        self.rejects("changed verdict attribution", lambda x: x["verdict"].__setitem__("checkpoint_id", x["revised"]["checkpoint"]["checkpoint_id"]), "C1-verdict-attribution")
        self.rejects("changed reopened checkpoint", lambda x: x["reopen"]["durable_after"]["checkpoint"].__setitem__("checkpoint_id", "forged-checkpoint"), "C2-durable-attribution")
        self.rejects("changed provider attempt", lambda x: x["reopen"]["after"]["provider"][0].__setitem__("attempt_id", "forged-attempt"), "C2-provider-duplicate")
        def disguised_provider(x):
            one = copy.deepcopy(x["reopen"]["before"]["provider"][0])
            one["attempt_id"] = "forged-attempt"
            x["final_counters"]["provider"].append(one)
        self.rejects("duplicate use disguised as another attempt", disguised_provider, "C2-provider-attribution")

    def test_forged_context_receipt_is_rejected(self):
        self.rejects("forged restored context receipt", lambda x: x["revised"]["receipt"].__setitem__("use_id", x["initial"]["binding"]["use_id"]), "C1-context-receipt")
