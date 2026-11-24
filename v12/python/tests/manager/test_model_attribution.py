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
