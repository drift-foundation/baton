"""N4a host guards with patch-only synthetic paths, never a qualified Codex row."""
import copy
from pathlib import Path
import unittest
from baton_v12 import provider_policy as policy
from baton_v12.contracts import ContractRefusal
from tests.manager import codex_fixtures as fixture
from tests.tools import test_pool as existing
from tools import pool, single_worker


class CodexComposition(unittest.TestCase):
    def setUp(self):
        self.fixture = existing.ComposingCase(methodName="runTest")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def compose(self, **changes):
        values = dict(provider_selection=fixture.SELECTED, cli_build="0.169.0",
                      credentials=["codex=operator-file:synthetic-only"])
        values.update(changes)
        return self.fixture.composing(**values)["worker"]

    def test_no_production_realization_can_be_composed(self):
        with self.assertRaises(pool.PoolRefusal):
            self.compose()

    def test_composition_binds_codex_slot_entry_and_role(self):
        with fixture.simulated(policy):
            worker = self.compose()
            given = pool.admitted(self.fixture.held, worker, "fixture-principal")["deployment"]
            Path(given["nominated_source"]).mkdir(parents=True)
            checked = single_worker._held(given)
            self.assertEqual(checked["credential_slots"], ["codex"])
            self.assertEqual(set(checked["credential_profile"]), {"codex"})
            adapter = checked["provider_contract"]["adapter"]
            self.assertEqual(adapter["entrypoint"], policy.ENTRYPOINTS["codex"])
            self.assertEqual(adapter["context_label"]["roles"], ["implementation"])
            self.assertEqual(adapter["participation_sources"], [])

    def test_composer_refuses_wrong_roles_and_slot_names(self):
        with fixture.simulated(policy):
            for role in ("review", "integration", "publication"):
                with self.subTest(role=role), self.assertRaises(pool.PoolRefusal):
                    self.compose(role=role)
            for credentials in (["claude=operator-file:synthetic-only"],
                    ["codex=operator-file:synthetic-only", "extra=operator-file:other"]):
                with self.subTest(credentials=credentials), self.assertRaises(pool.PoolRefusal):
                    self.compose(credentials=credentials)

    def test_revalidation_refuses_changed_role_slot_and_context(self):
        with fixture.simulated(policy):
            worker = self.compose()
            original = pool.admitted(self.fixture.held, worker, "fixture-principal")["deployment"]
            for changes in ({"launch_role": "review"}, {"launch_role": "integration"},
                            {"credential_slots": ["claude"]},
                            {"credential_profile": {"claude": original["credential_profile"]["codex"]}},
                            {"provider_context": {}}):
                given = dict(copy.deepcopy(original), **changes)
                with self.subTest(changes=changes), self.assertRaises(ContractRefusal):
                    single_worker._held(given, roles=("implementation", "review", "integration"))


TIERED = dict(fixture.SELECTED, service_tier="fast")


class CodexServiceTier(unittest.TestCase):
    """Optional service tier: synthetic realization, never a qualified row."""

    def setUp(self):
        self.fixture = existing.ComposingCase(methodName="runTest")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def compose(self, selected):
        return self.fixture.composing(provider_selection=selected, cli_build="0.169.0",
                                      credentials=["codex=operator-file:synthetic-only"])["worker"]

    def test_selection_accepts_only_a_realized_tier(self):
        with fixture.simulated(policy):
            self.assertEqual(policy.selection(TIERED), TIERED)
            self.assertEqual(policy.selection(fixture.SELECTED), fixture.SELECTED)
            for tier in (None, "", "flex", "FAST", "fast ", 1, True, ["fast"]):
                with self.subTest(tier=tier), self.assertRaises(policy.PolicyRefusal):
                    policy.selection(dict(fixture.SELECTED, service_tier=tier))
            with self.assertRaises(policy.PolicyRefusal):
                policy.selection(dict(TIERED, cli_build="0.170.0"))
            with self.assertRaises(policy.PolicyRefusal):
                policy.selection(dict(TIERED, extra="member"))
        claude = dict(provider="claude", requested_model="fixture-selector",
                      reported_identity="fixture-reported", cli_build="2.1.247")
        policy.selection(claude)
        with self.assertRaises(policy.PolicyRefusal):
            policy.selection(dict(claude, service_tier="fast"))
        with self.assertRaises(policy.PolicyRefusal):
            policy.selection(TIERED)  # No production Codex realization.

    def test_unset_keeps_every_identity_and_fast_is_a_different_one(self):
        with fixture.simulated(policy):
            plain = policy.adapter(fixture.SELECTED, network="bridge")
            tiered = policy.adapter(TIERED, network="bridge")
            self.assertNotIn("service_tier", plain["argv_policy"])
            self.assertEqual(tiered["argv_policy"]["service_tier"],
                             {"requested": "fast", "arguments": ["-c", 'service_tier="fast"']})
            self.assertEqual(dict(tiered, argv_policy=plain["argv_policy"]), plain)
            self.assertNotEqual(policy.digest(tiered), policy.digest(plain))
            self.assertEqual(policy.argv(plain, fixture.SELECTED, "work")[-3:], ["--model", "fixture-selector", "work"])
            self.assertEqual(policy.argv(tiered, TIERED, "work")[-5:],
                             ["--model", "fixture-selector", "-c", 'service_tier="fast"', "work"])
            # A tiered adapter under an untiered selection, and the reverse, disagree.
            for document, selected in ((tiered, fixture.SELECTED), (plain, TIERED)):
                with self.assertRaises(policy.PolicyRefusal):
                    policy.argv(document, selected, "work")
                with self.assertRaises(policy.PolicyRefusal):
                    policy.validate_adapter(document, selected, adapter_digest=policy.digest(document),
                                            tool_policy_digest=policy.digest(policy.POLICY))
            self.assertEqual(fixture.delivered(policy)["contract"]["adapter"], plain)

    def test_delivery_binds_the_tier_into_profile_and_contract(self):
        with fixture.simulated(policy):
            adapter = policy.adapter(TIERED, network="bridge")
            profile = {"schema": "baton.single-implementation-runtime-profile/2", "provider": "codex",
                       "model": TIERED["requested_model"], "reported_identity": TIERED["reported_identity"],
                       "cli_build": TIERED["cli_build"], "service_tier": "fast"}
            def deliver(selected, adapter, profile):
                return policy.delivery({"selection": selected, "adapter": adapter, "runtime_profile": profile},
                    adapter_digest=policy.digest(adapter), profile_digest=policy.digest(profile),
                    tool_policy_digest=policy.digest(policy.POLICY), authority_uuid="fixture-authority",
                    job_id="fixture-job", worker_id="fixture-worker", attempt_id="fixture-attempt")
            bound = deliver(TIERED, adapter, profile)
            self.assertEqual(bound["contract"]["selection"]["service_tier"], "fast")
            self.assertEqual(policy.validate_delivery(bound, {"attempt_id": "fixture-attempt", "job_id": "fixture-job"}), bound)
            untiered = {key: value for key, value in profile.items() if key != "service_tier"}
            plain = policy.adapter(fixture.SELECTED, network="bridge")
            for selected, document, held in ((TIERED, adapter, untiered), (TIERED, adapter, dict(profile, service_tier="flex")),
                                             (fixture.SELECTED, plain, profile)):
                with self.subTest(selected=selected, held=held), self.assertRaises(policy.PolicyRefusal):
                    deliver(selected, document, held)

    def test_configuration_composes_and_revalidates_the_tier(self):
        with fixture.simulated(policy):
            plain = self.compose(fixture.SELECTED)["deployment"]
            self.assertNotIn("service_tier", plain["provider_contract"]["selection"])
            self.assertNotIn("service_tier", plain["provider_contract"]["runtime_profile"])
            worker = self.compose(TIERED)
            given = pool.admitted(self.fixture.held, worker, "fixture-principal")["deployment"]
            contract = given["provider_contract"]
            self.assertEqual(contract["selection"]["service_tier"], "fast")
            self.assertEqual(contract["runtime_profile"]["service_tier"], "fast")
            self.assertEqual(contract["adapter"]["argv_policy"]["service_tier"]["arguments"], ["-c", 'service_tier="fast"'])
            for name in ("adapter_digest", "profile_digest"):
                self.assertNotEqual(given[name], plain[name])
            Path(given["nominated_source"]).mkdir(parents=True)
            self.assertEqual(single_worker._held(given)["provider_contract"], contract)
            # Dropping or changing the tier anywhere after composition is refused.
            for change in ("selection", "runtime_profile"):
                broken = copy.deepcopy(given)
                del broken["provider_contract"][change]["service_tier"]
                # Re-seal the profile so only the tier comparison can refuse.
                broken["profile_digest"] = policy.digest(broken["provider_contract"]["runtime_profile"])
                with self.subTest(change=change), self.assertRaises(ContractRefusal):
                    single_worker._held(broken)
            for tier in ("flex", None):
                with self.subTest(tier=tier), self.assertRaises(pool.PoolRefusal):
                    self.compose(dict(fixture.SELECTED, service_tier=tier))

    def test_requested_tier_is_never_reported_as_observed(self):
        from baton_v12.provider_policy import attribution
        with fixture.simulated(policy):
            adapter = policy.adapter(TIERED, network="bridge")
            delivered = {"contract": {"selection": TIERED, "adapter": adapter}, "attempt_id": "fixture-attempt",
                         "home_identity": {"job_id": "fixture-job"}}
            # Simulated output that merely echoes configuration and argv.
            raw = b'{"type":"result","subtype":"success","is_error":false,"service_tier":"fast","config":{"service_tier":"fast"}}'
            record = attribution.record(delivered, phase="implementation", evidenced_build="0.169.0", raw=raw)
            self.assertEqual(record["service_tier"], {"requested": "fast", "observed": None, "outcome": "missing"})
            self.assertEqual(attribution.validate(record, delivered, phase="implementation", raw=raw), record)
            self.assertTrue(attribution.diagnostic(record).endswith("; Service tier requested: fast; observed: no evidence"))
            with self.assertRaises(policy.PolicyRefusal):
                attribution.validate(dict(record, service_tier=dict(record["service_tier"], observed="fast", outcome="matched")),
                                     delivered, phase="implementation", raw=raw)
            plain = dict(delivered, contract={"selection": fixture.SELECTED, "adapter": policy.adapter(fixture.SELECTED, network="bridge")})
            untiered = attribution.record(plain, phase="implementation", evidenced_build="0.169.0", raw=raw)
            self.assertNotIn("service_tier", untiered)
            self.assertNotIn("Service tier", attribution.diagnostic(untiered))

    def test_compose_worker_operand_is_optional_and_forwarded(self):
        from unittest import mock
        base = ["compose-worker", "--deployment", "/synthetic/deployment.json", "--into", "/synthetic/worker.json",
                "--worker-id", "w", "--role", "implementation", "--participant", "p",
                "--image-reference", "i", "--image-digest", "sha256:" + "0" * 64, "--cli-build", "0.169.0",
                "--network", "n", "--credential-sources", "/synthetic/registry", "--credential", "codex=operator-file:synthetic-only",
                "--provider", "codex", "--requested-model", "fixture-selector", "--reported-identity", "fixture-reported",
                "--workspace-group", "1", "--task-document", "/synthetic/task.md", "--record", "/synthetic/record",
                "--legacy-verifier-layout"]
        for extra, expected in (([], fixture.SELECTED), (["--service-tier", "fast"], TIERED)):
            with self.subTest(extra=extra), mock.patch.object(pool, "compose") as compose:
                try:
                    pool.main(base + extra)
                except SystemExit as stop:
                    self.fail("compose-worker operands were refused: " + str(stop))
                self.assertEqual(compose.call_args.kwargs["provider_selection"], expected)
