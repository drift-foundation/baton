"""Deterministic interpretation proofs; connected owners are tested separately."""
import copy
import hashlib
import unittest
from baton_v12 import provider_policy as policy
from baton_v12.provider_policy import attribution as subject
from tests.manager import provider_fixtures as fixture


class Participation(unittest.TestCase):
    def setUp(self):
        self.delivery = fixture.delivery()

    def record(self, raw, **changes):
        return subject.record(self.delivery, phase="implementation", raw=raw,
                              **dict(dict(evidenced_build="2.1.247"), **changes))

    def test_4_9_union_sources_and_exact_mapping(self):
        sources = [{"field": "modelUsage", "kind": "keys"}, {"field": "measured", "kind": "value"}]
        self.delivery["contract"]["adapter"]["participation_sources"] = sources
        for names, extra, outcome in (([], {}, "missing"), (["fixture-reported"], {}, "matched"),
                ([], {"measured": "fixture-reported"}, "matched"),
                (["fixture-reported"], {"measured": "fixture-reported"}, "matched"),
                (["fixture-reported"], {"measured": "another"}, "matched"),
                (["another"], {"measured": "third"}, "conflicting")):
            with self.subTest(names=names, extra=extra):
                value = self.record(fixture.terminal(*names, **extra))
                self.assertEqual(value["outcome"], outcome)
                self.assertEqual(value["contributors"], sorted(set(names + list(extra.values()))))

    def test_3_5_missing_malformed_partial_oversize_and_build(self):
        for raw in (None, b"", b"{", b"null", b"[]", b'{}', b'"text"', b'x' * (subject.MAX_OUTPUT + 1),
                    b'{"type":"result","type":"result"}', b'\xff'):
            with self.subTest(raw=repr(raw)[:40]):
                self.assertEqual(self.record(raw)["outcome"], "missing")
        good = fixture.terminal("fixture-reported")
        self.assertEqual(self.record(good, partial=True)["outcome"], "missing")
        self.assertEqual(self.record(good, log_retained=False)["outcome"], "missing")
        self.assertEqual(self.record(good, evidenced_build=None)["outcome"], "missing")
        self.assertEqual(self.record(good, evidenced_build="2.1.999")["outcome"], "conflicting")

    def test_6_7_text_echo_error_and_unlisted_fields_never_contribute(self):
        for contributors in ([], ["another"]):
            raw = fixture.terminal(*contributors, result="fixture-reported", prompt="fixture-reported",
                tool_output="fixture-reported", model="fixture-reported", config={"model": "fixture-reported"})
            value = self.record(raw)
            self.assertEqual(value["contributors"], contributors)
            self.assertEqual(value["outcome"], "conflicting" if contributors else "missing")
        for changes in ({"type": "configuration"}, {"subtype": "error"}, {"is_error": True}):
            self.assertEqual(self.record(fixture.terminal("fixture-reported", **changes))["outcome"], "missing")

    def test_8_10_unrestricted_contributors_but_case_prefix_suffix_do_not_match(self):
        self.assertEqual(self.record(fixture.terminal("fixture-reported", "any-other", "third"))["outcome"], "matched")
        for name in ("Fixture-reported", "fixture-reported-extra", "prefix-fixture-reported"):
            self.assertEqual(self.record(fixture.terminal(name))["outcome"], "conflicting")

    def test_11_12_normalized_participation_and_exact_retained_byte_digest(self):
        first = fixture.terminal("fixture-reported", "another")
        second = fixture.terminal("another", "fixture-reported", usage={"cost": 999})
        a, b = self.record(first), self.record(second)
        for key in ("contributors", "contributor_sources", "mapped_identity", "outcome"):
            self.assertEqual(a[key], b[key])
        self.assertNotEqual(a["evidence"]["digest"], b["evidence"]["digest"])
        self.assertEqual(a["evidence"]["digest"], "sha256:" + hashlib.sha256(first).hexdigest())
        self.assertEqual(a, self.record(first))
        other = copy.deepcopy(self.delivery); other["attempt_id"] = "another-attempt"
        self.assertNotEqual(a["attempt_id"], subject.record(other, phase="implementation", evidenced_build="2.1.247", raw=first)["attempt_id"])
        self.assertNotIn("cost", str(a)); self.assertNotIn("Tokens", str(a))

    def test_15_altered_binding_or_raw_is_refused(self):
        raw = fixture.terminal("fixture-reported")
        value = self.record(raw)
        for key in ("attempt_id", "job_id", "phase", "provider", "mapped_identity", "selected_cli_build"):
            with self.subTest(key=key), self.assertRaises(policy.PolicyRefusal):
                subject.validate(dict(value, **{key: "another"}), self.delivery, phase="implementation", raw=raw)
        with self.assertRaises(policy.PolicyRefusal):
            subject.validate(value, self.delivery, phase="implementation", raw=fixture.terminal("another"))

    def test_18_19_diagnostic_words_and_legacy_default(self):
        value = subject.diagnostic(self.record(fixture.terminal("fixture-reported", "another")))
        for words in ("Requested:", "mapped identity:", "Reported contributors:", "Requested model reported: yes", "CLI build selected:", "CLI build evidenced:", "matched"):
            self.assertIn(words, value)
        for prohibited in ("primary", "helper", "share"):
            self.assertNotIn(prohibited, value)
        self.assertEqual(subject.diagnostic(None), "Requested: not selected (account default)")

    def test_21_participation_sources_are_adapter_identity(self):
        adapter = self.delivery["contract"]["adapter"]
        changed = copy.deepcopy(adapter); changed["participation_sources"].append({"field": "measured", "kind": "value"})
        self.assertNotEqual(policy.digest(changed), policy.digest(adapter))
        with self.assertRaises(policy.PolicyRefusal):
            policy.validate_adapter(changed, self.delivery["contract"]["selection"], adapter_digest=policy.digest(changed), tool_policy_digest=policy.digest(policy.POLICY))

    def test_1_model_selection_changes_only_worker_profile_identity(self):
        a_selected, a = fixture.identities()
        b_selected, b = fixture.identities(requested_model="other-selector", reported_identity="other-exact-id")
        self.assertNotEqual(a["profile_digest"], b["profile_digest"])
        self.assertEqual(a["adapter_digest"], b["adapter_digest"])
        self.assertEqual(a["policy_digest"], b["policy_digest"])
        for member in ("requested_model", "reported_identity"):
            with self.assertRaises(policy.PolicyRefusal):
                fixture.identities(**{member: ""})


class BuildProbe(unittest.TestCase):
    def test_3_probe_is_bounded_and_never_invocation_start_evidence(self):
        import os
        import subprocess
        from tests.tools import test_stage_execution  # worker package import path
        import claude_agent
        for raw, status, expected in ((b"2.1.247 (Claude Code)\n", 0, "2.1.247"),
                (b"2.1.999\n", 0, "2.1.999"), (b"bad", 0, None), (b"2.1.247\n", 1, None),
                (b"2.1.247\n" + b"x" * 100000, 0, None), (b"\xff", 0, None)):
            calls = []
            def runner(argv, **options):
                calls.append(argv)
                self.assertEqual(options["stdin"], subprocess.DEVNULL)
                self.assertEqual(options["timeout"], 5)
                os.write(options["stdout"], raw)
                return subprocess.CompletedProcess(argv, status)
            with self.subTest(raw=raw[:20], status=status):
                agent = claude_agent.ClaudeAgent(run=runner)
                self.assertEqual(agent.provider_version({}, "."), expected)
                self.assertEqual(calls, [["claude", "--version"]])
                self.assertIsNone(agent._invocation)


class ConfiguredCodex(unittest.TestCase):
    def setUp(self):
        import json
        from pathlib import Path
        from tests.manager import codex_fixtures
        self.enterContext(codex_fixtures.simulated(policy))
        self.delivery, self.invocation = codex_fixtures.configured(policy)
        self.raw = (Path(__file__).parent / "fixtures/codex-0.169.0/turn-success.sanitized.jsonl").read_bytes()
        self.json = json

    def record(self, **changes):
        args = dict(phase="implementation", evidenced_build="0.169.0", raw=self.raw, invocation=self.invocation)
        args.update(changes)
        return subject.record(self.delivery, **args)

    def validate(self, claim, **changes):
        args = dict(phase="implementation", raw=self.raw, invocation_raw=self.json.dumps(self.invocation).encode())
        args.update(changes)
        return subject.validate(claim, self.delivery, **args)

    def test_A1_labelled_configuration_acceptance_and_unknown_participation(self):
        value = self.record()
        self.assertTrue(subject.acceptable(value))
        self.assertEqual(value["outcome"], "configured-model-accepted")
        self.assertEqual(value["actual_participation"], "unknown")
        self.assertEqual(value["contributors"], [])
        self.assertEqual(self.validate(value), value)
        text = subject.diagnostic(value)
        for word in ("Configured model accepted", "actual participation unknown", "no reroute observed", "adapter-recorded, host-validated"):
            self.assertIn(word, text)
        self.assertNotIn("rerouting proved absent", text)
        self.assertNotIn("SYNTHETIC PRIVATE PROMPT", self.json.dumps(value))

    def test_A2_missing_configuration_build_image_stream_and_receipt_hold(self):
        for changes in (dict(invocation=None), dict(evidenced_build=None), dict(raw=None), dict(partial=True), dict(log_retained=False)):
            with self.subTest(changes=changes): self.assertFalse(subject.acceptable(self.record(**changes)))
        for key in self.invocation:
            broken = dict(self.invocation); del broken[key]
            self.assertFalse(subject.acceptable(self.record(invocation=broken)))
        del self.delivery["contract"]["runtime_profile"]["image_digest"]
        self.assertFalse(subject.acceptable(self.record()))

    def test_A3_changed_receipt_and_identity_refuse(self):
        value = self.record()
        for key in ("attempt_id", "job_id", "phase", "requested_model", "image_digest", "selection_digest"):
            with self.subTest(key=key), self.assertRaises(policy.PolicyRefusal):
                self.validate(dict(value, **{key: "wrong"}))
        for key, changed in (("prompt_digest", "sha256:"+"f"*64), ("argv_digest", "sha256:"+"f"*64),
                             ("context_label", {}), ("argv_prefix", ["codex", "--model", "wrong"])):
            altered = copy.deepcopy(value); altered["invocation"][key] = changed
            with self.subTest(key=key), self.assertRaises(policy.PolicyRefusal): self.validate(altered)
        with self.assertRaises(policy.PolicyRefusal): self.validate(value, invocation_raw=None)
        with self.assertRaises(policy.PolicyRefusal): self.validate(value, invocation_raw=b"{}")
        with self.assertRaises(policy.PolicyRefusal): self.validate(value, raw=self.raw+b"{}\n")

    def test_R1_internally_consistent_unqualified_build_refuses(self):
        selected = self.delivery["contract"]["selection"]
        profile = self.delivery["contract"]["runtime_profile"]
        selected["cli_build"] = profile["cli_build"] = "0.172.0"
        self.delivery["profile_digest"] = policy.digest(profile)
        self.invocation["evidenced_cli_build"] = "0.172.0"
        self.invocation["selection_digest"] = policy.digest(self.delivery)
        value = self.record(evidenced_build="0.172.0")
        self.assertEqual(value["outcome"], "unqualified-build")
        self.assertFalse(subject.acceptable(value))

    def test_R2_basis_is_admitted_provider_not_claim(self):
        value = self.record()
        for changes in (dict(basis="participation"), dict(contributors=["invented"]),
                        dict(contributor_sources={"invented":["configuration"]}), dict(schema=subject.SCHEMA)):
            with self.subTest(changes=changes), self.assertRaises(policy.PolicyRefusal):
                self.validate(dict(value, **changes))
        with self.assertRaises(policy.PolicyRefusal):
            subject.validate(value, fixture.delivery(), phase="implementation", raw=self.raw)
        for schema in ("baton.model-attribution/3", None):
            with self.assertRaises(policy.PolicyRefusal): self.validate(dict(value, schema=schema))

    def test_A4_R3_source_defined_reroute_refuses_even_exit_zero(self):
        events = [self.json.loads(x) for x in self.raw.split(b"\n") if x]
        # Synthetic negative, exact source-defined error-item surface, NOT live output.
        events.insert(2, {"type":"item.completed", "item":{"id":"synthetic-reroute", "type":"error",
            "message":"model rerouted: requested -> alternate (HighRiskCyberActivity)"}})
        raw = ("\n".join(self.json.dumps(x) for x in events)+"\n").encode()
        value = self.record(raw=raw)
        self.assertEqual(value["outcome"], "rerouted")
        self.assertFalse(subject.acceptable(value))
        self.assertEqual(value["reroute_observation"], "reroute observed")
        self.assertEqual(self.validate(value, raw=raw), value)

    def test_A5_C1_unicode_inside_text_and_prose_are_opaque(self):
        events = [self.json.loads(x) for x in self.raw.split(b"\n") if x]
        events[-2]["item"]["text"] = "separators \u0085\u2028\u2029 model rerouted: a -> b (HighRiskCyberActivity)"
        raw = ("\n".join(self.json.dumps(x, ensure_ascii=False) for x in events)+"\n").encode()
        self.assertTrue(subject.acceptable(self.record(raw=raw)))
        self.assertEqual(self.record(raw=raw[:-1])["reroute_observation"], "reroute observation incomplete")
        for raw in (self.raw + b"{}\n", self.raw.replace(b"\n", b"\u2028"), b"{}\n"):
            self.assertFalse(subject.acceptable(self.record(raw=raw)))

    def test_A6_Claude_stronger_and_A7_legacy_unchanged(self):
        given = fixture.delivery()
        for names, outcome in ((["fixture-reported", "other"], "matched"), (["other"], "conflicting"), ([], "missing")):
            raw = fixture.terminal(*names)
            value = subject.record(given, phase="review", evidenced_build="2.1.247", raw=raw)
            self.assertEqual(value["schema"], subject.SCHEMA)
            self.assertEqual(value["outcome"], outcome)
            self.assertEqual(value["contributors"], sorted(names))
            self.assertEqual(subject.validate(value, given, phase="review", raw=raw), value)
        self.assertEqual(subject.diagnostic(None), "Requested: not selected (account default)")


    def test_receipt_cannot_be_rebound_to_another_attempt_or_probe(self):
        original = copy.deepcopy(self.invocation)
        self.delivery["attempt_id"] = "other-attempt"
        self.assertFalse(subject.acceptable(self.record(invocation=original)))
        self.delivery["attempt_id"] = "fixture-attempt"
        self.invocation["evidenced_cli_build"] = "0.172.0"
        self.assertFalse(subject.acceptable(self.record()))


    def test_missing_public_configuration_members_and_failed_environment_hold(self):
        value = self.record()
        for key in ("requested_model", "image_digest", "selected_cli_build", "evidenced_cli_build", "evidence", "selection_digest"):
            changed = copy.deepcopy(value); del changed[key]
            with self.subTest(key=key), self.assertRaises(policy.PolicyRefusal): self.validate(changed)
        for key, member in (("environment_validated", False), ("status", 1), ("status", True)):
            changed = dict(self.invocation, **{key: member})
            self.assertFalse(subject.acceptable(self.record(invocation=changed)))
