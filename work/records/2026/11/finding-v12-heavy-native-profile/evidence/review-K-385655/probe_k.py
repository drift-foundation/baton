"""K independent probes for W385649 candidate 5771ed8d (review-only, deterministic, no live provider)."""
import copy, json, sys, unittest
from types import SimpleNamespace

from baton_v12.job_manager import job_control, execution_limits
from baton_v12.contracts.errors import ContractRefusal


class K(unittest.TestCase):

    def test_P1_resolved_bytes_of_old_profiles(self):
        out = {p: job_control.resolved(p) for p in ("documentation/1", "native-handoff/1")}
        out["continuations_old"] = {p: job_control.CONTINUATIONS[p] for p in ("documentation/1", "native-handoff/1")}
        out["generations"] = execution_limits.GENERATIONS
        print("P1-BYTES", json.dumps(out, sort_keys=True, separators=(",", ":")))

    def test_P2_cli_request_shape(self):
        from tools import job_manager as cli
        taken = SimpleNamespace(task="task-1", statement="do it", source="installed",
            work_scope=["v12/python/src"], test_scope=[], acceptance=["ok"], template=None,
            job_id=None, submission_id=None, provider_turn_seconds=7200,
            verification_command_seconds=None, control_profile="native-handoff-heavy/1")
        req = cli._creation_request(taken)
        print("P2-CLI", json.dumps({k: req.get(k) for k in ("control", "overrides")}, sort_keys=True))
        self.assertEqual(req["control"], {"profile": "native-handoff-heavy/1"})
        self.assertEqual(req["overrides"], {"execution_limits": {"provider_turn_seconds": 7200}})

    def _connected(self, profile, limits, tamper=None):
        from tests.job_manager import test_creation as c
        from tests.tools import test_execution_limits as worker
        from tools import single_worker
        from baton_v12.worker_manager import launch
        case = c.CreationCase("setUp"); case.setUp()
        try:
            kw = {"control": {"profile": profile}}
            if limits: kw["overrides"] = {"execution_limits": limits}
            created = case.created(request=c.request(**kw))
            given = {"input_manifest": {"manifest_digest": "sha256:" + "3" * 64},
                     "policy_digest": "sha256:" + "2" * 64}
            reader = SimpleNamespace(execution_context=single_worker.job_execution_reader(case.jobs),
                                     given=given, _given_for=lambda stage: given)
            adapter = worker.TheAdapterHandsTheCommandWhatWasConfigured()
            got = {}
            for role in ("implementation", "review"):
                ctx = single_worker._SingleWorker._job_execution(reader, {"job_id": created["job_id"], "attempt_id": "a-" + role})
                if tamper:
                    ctx = copy.deepcopy(ctx); ctx["execution_limits"]["boundaries"]["provider_turn"]["seconds"] = tamper
                d = launch.launch_document(session="k-" + role, contract="k-task", role=role, transport=None, job_execution=ctx)
                seen = worker.baton_worker.launched(d, place="/run/baton/launch.json")
                agent, cap = adapter.production(seen)
                agent._provider({"verification": ["fake"]}, "/unused", "/unused", {}, prompt="p")
                agent._verify({"verification": ["fake"]}, "/unused", {}, ())
                got[role] = cap
                got[role + "-token"] = execution_limits.task_token_seconds(ctx["execution_limits"])
            got["job_seconds"] = created["control"]["resolved"]["job_seconds"]
            got["stage_seconds"] = created["control"]["resolved"]["stage_seconds"]
            return got
        finally:
            case.doCleanups()

    def test_P3_connected_discriminates(self):
        heavy = self._connected("native-handoff-heavy/1", {"provider_turn_seconds": 7200})
        base = self._connected("native-handoff/1", None)
        print("P3-HEAVY", json.dumps(heavy, sort_keys=True)); print("P3-NATIVE", json.dumps(base, sort_keys=True))
        self.assertEqual(heavy["implementation"], [7200, 900]); self.assertEqual(heavy["review"], [7200, 900])
        self.assertEqual(base["implementation"], [3600, 900]); self.assertEqual(base["review"], [3600, 900])
        self.assertEqual((heavy["job_seconds"], heavy["stage_seconds"]), (21600, 9000))

    def test_P4_runner_reads_delivered_document(self):
        try:
            t = self._connected("native-handoff-heavy/1", {"provider_turn_seconds": 7200}, tamper=5000)
            print("P4-TAMPER", json.dumps(t, sort_keys=True))
        except Exception as e:
            print("P4-TAMPER-REFUSED", type(e).__name__, str(e)[:300])

    def test_P5_cli_request_through_real_creation(self):
        from tests.job_manager import test_creation as c
        case = c.CreationCase("setUp"); case.setUp()
        try:
            for profile, limits, ok in (("native-handoff-heavy/1", {"provider_turn_seconds": 7200}, True),
                                        ("native-handoff-heavy/1", None, False),
                                        ("native-handoff-heavy/1", {"provider_turn_seconds": 7199}, False),
                                        ("native-handoff-heavy/1", {"provider_turn_seconds": 7200, "verification_command_seconds": 900}, True),
                                        ("native-handoff/1", {"provider_turn_seconds": 7200}, False),
                                        ("native-handoff-heavy/2", {"provider_turn_seconds": 7200}, False)):
                kw = {"control": {"profile": profile}, "task": {"task_id": f"t-{profile}-{json.dumps(limits)}".replace("/", "_").replace(" ", "")[:60], "statement": "s"}}
                if limits: kw["overrides"] = {"execution_limits": limits}
                try:
                    r = case.created(request=c.request(**kw)); res = ("admitted", r["control"]["resolved"])
                except ContractRefusal as e:
                    res = ("refused", str(e)[:160])
                print("P5", profile, limits, res[0], json.dumps(res[1], sort_keys=True) if res[0] == "admitted" else res[1])
                self.assertEqual(res[0] == "admitted", ok, (profile, limits, res))
        finally:
            case.doCleanups()


if __name__ == "__main__":
    unittest.main(verbosity=2)
