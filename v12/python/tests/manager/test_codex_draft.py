"""N4a joined adapter: offline boundaries, not provider qualification.

Registered in manager-pure after the D-first checkpoint.
Mocked delivery contracts exercise only subclass guards; no mocked provider
success or credential layout is presented as exact-build evidence.
"""
import hashlib
import json
from pathlib import Path
import shlex
import sys
import unittest
from unittest import mock

WORKER = Path(__file__).resolve().parents[3] / "worker"
sys.path.insert(0, str(WORKER))
sys.path.insert(0, str(WORKER.parent / "python" / "src" / "baton_v12"))
import claude_agent
import codex_agent
import codex_entry
import dogfood_entry

FIXTURES = Path(__file__).parent / "fixtures" / "codex-0.169.0"


def delivery(roles=None, build=codex_agent.CLI_BUILD):
    """Synthetic post-validation contract, only for guard isolation."""
    return {"contract": {"adapter": {"provider": "codex", "context_label": {
        "roles": ["implementation"] if roles is None else roles}},
        "selection": {"cli_build": build, "requested_model": "selected-model"}}}


class CodexDraft(unittest.TestCase):
    def setUp(self):
        self.run = mock.Mock(side_effect=AssertionError("provider must not run"))
        self.agent = codex_agent.CodexAgent(run=self.run)

    def test_r1_refuses_before_home_or_runner(self):
        for prompt in ("", " ", "\n", "-", "--help", "-x", "resume", "fork",
                       "review", "help", None, 1, "text\0text"):
            with self.subTest(prompt=prompt), mock.patch.object(
                    self.agent, "_prepared_home") as home:
                with self.assertRaises(codex_agent.TaskRefusal):
                    self.agent.invoke_provider(prompt=prompt, room="/not-used")
                with self.assertRaises(codex_agent.TaskRefusal):
                    self.agent.provider_argv(prompt, model="explicit")
                home.assert_not_called()
        self.run.assert_not_called()

    def test_prompt_is_one_literal_operand(self):
        for prompt in ("[implementation] do work", "review this", "resume ",
                       "a\nb", "$(never); `never` 'quoted'", " help"):
            with self.subTest(prompt=prompt):
                self.assertEqual(self.agent.provider_argv(prompt, model="explicit"),
                    ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox",
                     "--ignore-user-config", "--ignore-rules", "--json",
                     "--model", "explicit", prompt])
        self.run.assert_not_called()

    def test_model_has_no_implicit_default(self):
        with self.assertRaises(codex_agent.TaskRefusal):
            self.agent.provider_argv("work")
        with mock.patch.object(self.agent, "_provider_selection", return_value=delivery()):
            self.assertEqual(self.agent.provider_argv("work")[-3:],
                             ["--model", "selected-model", "work"])

    def test_service_tier_fast_is_one_exact_config_pair_before_the_prompt(self):
        argv = self.agent.provider_argv("work", model="explicit", service_tier="fast")
        self.assertEqual(argv, ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox",
                                "--ignore-user-config", "--ignore-rules", "--json",
                                "--model", "explicit", "-c", 'service_tier="fast"', "work"])
        self.assertIn(""" -c 'service_tier="fast"' work""", shlex.join(argv))
        # The retained exact-build help evidences the option, not the key.
        help_text = (FIXTURES / "exec-help.txt").read_text()
        self.assertIn("-c, --config <key=value>", help_text)
        self.assertIn("parsed\n          as TOML", help_text)
        self.assertNotIn("service_tier", help_text)
        self.run.assert_not_called()

    def test_unset_service_tier_keeps_the_existing_argv(self):
        expected = ["codex", "exec", "--dangerously-bypass-approvals-and-sandbox",
                    "--ignore-user-config", "--ignore-rules", "--json", "--model", "explicit", "work"]
        self.assertEqual(self.agent.provider_argv("work", model="explicit"), expected)
        self.assertEqual(self.agent.provider_argv("work", model="explicit", service_tier=None), expected)
        with mock.patch.object(self.agent, "_provider_selection", return_value=delivery()):
            self.assertEqual(self.agent.provider_argv("work"), expected[:-3] + ["--model", "selected-model", "work"])

    def test_unrealized_service_tiers_refuse(self):
        for tier in ("flex", "FAST", "fast ", "", "priority", "default", 1, True, ["fast"], '"fast"'):
            with self.subTest(tier=tier), self.assertRaises(codex_agent.TaskRefusal):
                self.agent.provider_argv("work", model="explicit", service_tier=tier)
        with mock.patch.object(codex_agent, "CLI_BUILD", "0.170.0"):
            with self.assertRaises(codex_agent.TaskRefusal):
                self.agent.provider_argv("work", model="explicit", service_tier="fast")
        self.run.assert_not_called()

    def test_launched_worker_takes_the_tier_only_from_its_selection(self):
        tiered = delivery()
        tiered["contract"]["selection"]["service_tier"] = "fast"
        tail = ["--model", "selected-model", "-c", 'service_tier="fast"', "work"]
        self.agent._seen = {"schema": "baton.worker-launch/6", "role": "implementation"}
        with mock.patch.object(self.agent, "_provider_selection", return_value=tiered):
            # Both calls the shared runner makes: without and with the model.
            self.assertEqual(self.agent.provider_argv("work")[-5:], tail)
            self.assertEqual(self.agent.provider_argv("work", model="selected-model")[-5:], tail)
            for operand in ("fast", None):
                with self.subTest(operand=operand), self.assertRaises(codex_agent.TaskRefusal):
                    self.agent.provider_argv("work", model="selected-model", service_tier=operand)
        with mock.patch.object(self.agent, "_provider_selection", return_value=delivery()):
            self.assertEqual(self.agent.provider_argv("work", model="selected-model")[-3:], tail[:2] + ["work"])
        self.agent._seen = None
        with mock.patch.object(self.agent, "_provider_selection", return_value=tiered):
            with self.assertRaises(codex_agent.TaskRefusal):
                self.agent.provider_argv("work", service_tier="fast")
        self.run.assert_not_called()

    def test_invalid_explicit_models_refuse(self):
        for model in ("", "-x", "a\nb", "a\0b", 3, "x" * 257):
            with self.subTest(model=model), self.assertRaises(codex_agent.TaskRefusal):
                self.agent.provider_argv("work", model=model)
        self.run.assert_not_called()

    def test_legacy_and_reuse_refuse_before_shared_selection(self):
        for seen in ({}, {"schema": "baton.worker-launch/5"},
                     {"schema": "baton.worker-launch/6", "provider_context": {}},
                     {"schema": "baton.worker-launch/6", "provider_context": "reuse"}):
            self.agent._seen = seen
            with self.subTest(seen=seen), mock.patch.object(
                    claude_agent.ClaudeAgent, "_provider_selection") as parent:
                with self.assertRaises(codex_agent.TaskRefusal):
                    self.agent._provider_selection()
                parent.assert_not_called()

    def test_role_and_build_guards_on_simulated_validated_delivery(self):
        for role, roles, build in (("review", ["implementation"], "0.169.0"),
                ("implementation", [], "0.169.0"),
                ("implementation", ["implementation"], "0.168.0")):
            self.agent._seen = {"schema": "baton.worker-launch/6", "role": role}
            with self.subTest(role=role, roles=roles, build=build), mock.patch.object(
                    claude_agent.ClaudeAgent, "_provider_selection",
                    return_value=delivery(roles, build)):
                with self.assertRaises(codex_agent.TaskRefusal):
                    self.agent._provider_selection()

    def test_selected_implementation_guard_preserves_contract(self):
        selected = delivery()
        self.agent._seen = {"schema": "baton.worker-launch/6", "role": "implementation"}
        with mock.patch.object(claude_agent.ClaudeAgent, "_provider_selection",
                               return_value=selected):
            self.assertIs(self.agent._provider_selection(), selected)
        self.run.assert_not_called()

    def test_home_and_session_layout_stay_gated(self):
        with self.assertRaises(codex_agent.TaskRefusal):
            self.agent._prepared_home(Path("/not-used"))
        with self.assertRaises(codex_agent.TaskRefusal):
            self.agent.provider_session_root(Path("/not-used"))
        self.run.assert_not_called()

    def test_no_terminal_shape_or_exit_code_is_success(self):
        # Synthetic refusal probes, never a claim about actual Codex JSONL.
        for status in (0, 1, -15):
            for record in (None, b"", b"{broken", {"type": "result", "is_error": False}):
                for partial in (False, True):
                    with self.subTest(status=status, record=record, partial=partial):
                        result = self.agent.provider_terminal(status, record, partial=partial)
                        self.assertIs(result["ok"], False)
                        self.assertEqual(result["failure_reason"], codex_agent.UNCLASSIFIED)
                        self.assertEqual(result["status"], status)
                        self.assertNotIn("record", result)


class EntryDraft(unittest.TestCase):
    def test_real_invalid_delivery_never_constructs_adapter(self):
        build = mock.Mock(side_effect=AssertionError("invalid launch constructed adapter"))
        with mock.patch.object(dogfood_entry, "main", return_value=3) as main:
            self.assertEqual(codex_entry.production(place="/not-used", read=lambda p: {},
                                                   build=build), 3)
        build.assert_not_called()
        main.assert_called_once_with(agent=None, place="/not-used")

    def test_simulated_valid_delivery_constructs_only_after_validation(self):
        order = []
        agent = object()
        def read(place):
            order.append("read")
            return {"synthetic": True}
        def validate(document, place):
            self.assertEqual(order, ["read"])
            order.append("validated")
        def build():
            self.assertEqual(order, ["read", "validated"])
            order.append("built")
            return agent
        with mock.patch.object(dogfood_entry.baton_worker, "launched", side_effect=validate), \
                mock.patch.object(codex_entry, "CodexAgent", side_effect=build), \
                mock.patch.object(dogfood_entry, "main", return_value=7) as main:
            self.assertEqual(codex_entry.production(place="/not-used", read=read,
                command_root="commands", event_root="events"), 7)
        main.assert_called_once_with(agent=agent, place="/not-used",
                                     command_root="commands", event_root="events")
        self.assertEqual(order, ["read", "validated", "built"])

    def test_existing_supervisor_owns_process_lifecycle(self):
        with mock.patch.object(dogfood_entry, "supervised", return_value=9) as supervisor:
            self.assertEqual(codex_entry.main(), 9)
        supervisor.assert_called_once_with(run=codex_entry.production)


class InventoryAndRecipe(unittest.TestCase):
    def test_retained_inventory_bytes_and_options(self):
        provenance = json.loads((FIXTURES / "provenance.json").read_text())
        for name, member in provenance["files"].items():
            self.assertEqual(hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(),
                             member["sha256"])
        self.assertEqual((FIXTURES / "version.txt").read_bytes(), b"codex-cli 0.169.0\n")
        help_text = (FIXTURES / "exec-help.txt").read_text()
        for option in (*codex_agent.ARGUMENTS[1:], "--model"):
            self.assertIn(option, help_text)
        for command in codex_agent.EXEC_COMMANDS:
            self.assertRegex(help_text, r"(?m)^  " + command + r"\s")

    def test_recipe_is_exact_pinned_source_and_reuses_worker_boundary(self):
        def instructions(name):
            lines = (WORKER / name).read_text().replace("\\\n", " ").splitlines()
            return [line.strip() for line in lines if line.strip() and not line.startswith("#")]
        draft = instructions("Dockerfile.codex")
        prior = instructions("Dockerfile.claude")
        self.assertIn('ENTRYPOINT ["python3", "/opt/baton/codex_entry.py"]', draft)
        self.assertIn("USER 65532:65532", draft)
        install = [line for line in draft if line.startswith("RUN npm")]
        self.assertEqual(len(install), 1)
        self.assertIn('"@openai/codex@0.169.0"', install[0])
        self.assertFalse(any(line.startswith("ARG ") for line in draft))
        copies = [shlex.split(line)[1:] for line in draft if line.startswith("COPY ")]
        prior_copies = [shlex.split(line)[1:] for line in prior if line.startswith("COPY ")]
        for item in prior_copies:
            self.assertIn(item, copies)
        for source, target in copies:
            self.assertTrue((WORKER.parent / source).exists(), source)
        self.assertIn(["worker/codex_agent.py", "/opt/baton/codex_agent.py"], copies)
        self.assertIn(["worker/codex_entry.py", "/opt/baton/codex_entry.py"], copies)
        for line in prior:
            if "verifier" in line or line.startswith("ENV "):
                self.assertIn(line, draft)


class JoinedCodex(unittest.TestCase):
    def test_production_mapping_is_explicit_and_roles_remain_bounded(self):
        import provider_policy as policy
        from tests.manager import codex_fixtures as fixture
        adapter = policy.adapter(fixture.SELECTED, network="bridge")
        self.assertEqual(adapter["credential"], {"mode": "seeded-retained", "path": "codex/auth.json"})
        self.assertEqual(adapter["environment_policy"]["CODEX_HOME"], policy.HOME + "/codex")
        self.assertEqual(adapter["managed_entries"][0]["path"], "instructions/WORKER.md")
        self.assertEqual(policy.LABEL_ROLES["codex"], ["implementation"])
        for role in ("review", "integration"):
            with self.assertRaises(policy.PolicyRefusal): policy.context_label(adapter, role)
        with self.assertRaises(policy.PolicyRefusal): policy.adapter(dict(fixture.SELECTED, provider="unknown"), network="bridge")

    def test_exact_version_decode_and_probe_gate(self):
        import os
        import subprocess
        raw = (FIXTURES / "version.txt").read_bytes()
        agent = codex_agent.CodexAgent()
        self.assertEqual(agent.decode_provider_version(raw), "0.169.0")
        for invalid in (b"0.169.0", b"0.169.0 (Claude Code)", b"codex-cli 0.169.0 extra", b"\xff"):
            self.assertIsNone(agent.decode_provider_version(invalid))
        for output in (raw, b"codex-cli 0.168.0\n", b"unknown", b"x" * 1025):
            calls = []
            def run(argv, **kw):
                calls.append(argv)
                os.write(kw["stdout"], output)
                return subprocess.CompletedProcess(argv, 0)
            agent = codex_agent.CodexAgent(run=run)
            if output == raw:
                self.assertEqual(agent.provider_version({}, "/not-used"), "0.169.0")
            else:
                with self.assertRaises(codex_agent.TaskRefusal):
                    agent.provider_version({}, "/not-used")
            self.assertEqual(calls, [["codex", "--version"]])
        claude = claude_agent.ClaudeAgent()
        self.assertEqual(claude.decode_provider_version(b"2.1.247 (Claude Code)\n"), "2.1.247")
        self.assertEqual(claude.decode_provider_version(b"2.1.247\n"), "2.1.247")
        self.assertIsNone(claude.decode_provider_version(raw))

    def test_joined_home_label_argv_and_record_use_shared_owners(self):
        import os
        import tempfile
        import provider_policy as policy
        from tests.manager import codex_fixtures as fixture
        from tests.manager.disk_roots import disk_backed_root
        with tempfile.TemporaryDirectory(dir=disk_backed_root()) as root:
            home = Path(root, "home"); home.mkdir(mode=0o700)
            slots = Path(root, "slots"); slots.mkdir()
            (slots / "codex").write_bytes(b"SYNTHETIC SEED ONLY")
            with fixture.simulated(policy, home=home), mock.patch.object(claude_agent, "CREDENTIAL_ROOT", str(slots)):
                delivery = fixture.delivered(policy)
                agent = codex_agent.CodexAgent(run=mock.Mock(side_effect=AssertionError("no process")))
                agent._seen = {"schema": "baton.worker-launch/6", "role": "implementation",
                    "provider_selection": delivery, "job_execution": {"attempt_id": "fixture-attempt", "job_id": "fixture-job"}}
                self.assertEqual(agent._prepared_home(root), str(home))
                self.assertEqual((home / "fixture/credential").read_bytes(), b"SYNTHETIC SEED ONLY")
                self.assertEqual((home / "fixture/instructions.md").read_bytes(), policy.worker_instructions())
                (home / "fixture/credential").write_bytes(b"SYNTHETIC REFRESH")
                (home / "fixture/instructions.md").write_bytes(b"changed")
                (home / "provider-owned").write_bytes(b"keep")
                (slots / "codex").unlink()
                agent._prepared_home(root)
                self.assertEqual((home / "fixture/credential").read_bytes(), b"SYNTHETIC REFRESH")
                self.assertEqual((home / "provider-owned").read_bytes(), b"keep")
                self.assertEqual((home / "fixture/instructions.md").read_bytes(), policy.worker_instructions())
                adapter = delivery["contract"]["adapter"]
                self.assertEqual(adapter["entrypoint"], ["python3", "/opt/baton/codex_entry.py"])
                self.assertEqual(adapter["participation_sources"], [])
                self.assertEqual(agent.provider_credential_slot(delivery), "codex")
                # Normal _provider seam, no process or terminal success fixture.
                environment = dict(policy.ENVIRONMENT)
                with mock.patch.object(agent, "_resolved_bound", return_value={"seconds_bound": 10}), \
                        mock.patch.object(agent, "_revalidated_environment", return_value=environment), \
                        mock.patch.object(agent, "provider_version", return_value="0.169.0"), \
                        mock.patch.object(agent, "_ran_provider", return_value=(0, None, False)) as run:
                    result = agent._provider(None, str(home), root, environment, prompt="do the bounded task")
                labelled = policy.labelled(adapter, "implementation", "do the bounded task")
                self.assertEqual(run.call_args.args[0], policy.argv(adapter, fixture.SELECTED, labelled))
                self.assertEqual(agent._context_label, policy.context_record(adapter, "implementation"))
                self.assertFalse(result["ok"])
                self.assertEqual(result["failure_reason"], codex_agent.UNCLASSIFIED)
                self.assertNotEqual(result["attribution"]["outcome"], "matched")
                # Replay the sanitized observed stream at the normal provider seam.
                raw = (FIXTURES / "turn-success.sanitized.jsonl").read_bytes()
                agent._provider_raw_digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                agent._provider_log_retained = True
                with mock.patch.object(agent, "_resolved_bound", return_value={"seconds_bound": 10}), \
                        mock.patch.object(agent, "_revalidated_environment", return_value=environment), \
                        mock.patch.object(agent, "provider_version", return_value="0.169.0"), \
                        mock.patch.object(agent, "_ran_provider", return_value=(0, raw, False)):
                    completed = agent._provider(None, str(home), root, environment, prompt="do the bounded task")
                self.assertTrue(completed["ok"])
                self.assertEqual(completed["attribution"]["outcome"], "missing")
                self.assertEqual(completed["attribution"]["contributors"], [])
                # The worker validates the real delivered identity before role use.
                agent._seen["role"] = "review"
                with self.assertRaises(codex_agent.TaskRefusal):
                    agent._provider_selection()

    def test_bound_role_list_is_single_source(self):
        import provider_policy as policy
        from tests.manager import codex_fixtures as fixture
        with fixture.simulated(policy):
            adapter = policy.adapter(fixture.SELECTED, network="bridge")
            for role in ("review", "integration", "publication", None):
                with self.assertRaises(policy.PolicyRefusal):
                    policy.validate_execution(adapter, role)
            policy.validate_execution(adapter, "implementation")
            with self.assertRaises(policy.PolicyRefusal):
                policy.validate_execution(adapter, "implementation", {})
        # Changing a role in a bound document also changes adapter identity;
        # validation refuses even if somebody updates its digest themselves.
        with fixture.simulated(policy):
            adapter = policy.adapter(fixture.SELECTED, network="bridge")
            adapter["context_label"]["roles"] = ["review"]
            with self.assertRaises(policy.PolicyRefusal):
                policy.validate_adapter(adapter, fixture.SELECTED, adapter_digest=policy.digest(adapter),
                                        tool_policy_digest=policy.digest(policy.POLICY))


class CodexTerminalEvidence(unittest.TestCase):
    """Retained success; negative mutations are robustness tests, not live failures."""
    def setUp(self):
        self.agent = codex_agent.CodexAgent(run=mock.Mock(side_effect=AssertionError("no provider")))
        self.raw = (FIXTURES / "turn-success.sanitized.jsonl").read_bytes()
        self.events = [json.loads(line) for line in self.raw.splitlines()]

    def encoded(self, events):
        return ("\n".join(json.dumps(x) for x in events) + "\n").encode()

    def refuses(self, raw, status=0, partial=False):
        answer = self.agent.provider_terminal(status, raw, partial=partial)
        self.assertFalse(answer["ok"])
        self.assertEqual(answer["failure_reason"], codex_agent.UNCLASSIFIED)
        self.assertEqual(answer["status"], status)
        self.assertNotIn("record", answer)

    def test_retained_complete_turn_has_terminal_success_only(self):
        self.assertEqual(self.agent.provider_terminal(0, self.raw, partial=False),
                         dict(ok=True, status=0, failure_reason=None, why=None))
        self.agent._run.assert_not_called()

    def test_fixture_identity_and_projection_provenance(self):
        manifest = json.loads((FIXTURES / "turn-provenance.json").read_text())
        self.assertEqual(manifest["cli_build"], codex_agent.CLI_BUILD)
        self.assertEqual(manifest["exit_status"], 0)
        self.assertFalse(manifest["participation_evidence"])
        self.assertFalse(manifest["backend_identity_attested"])
        for name, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(), digest)
        self.assertNotIn(b"01a210b2", self.raw)
        self.assertNotIn(b"/home/", self.raw)
        self.assertNotIn(b"/var/tmp/", self.raw)

    def test_process_exit_alone_and_partial_never_succeed(self):
        for status in (1, -15, None, False, 0.0):
            with self.subTest(status=status): self.refuses(self.raw, status=status)
        for partial in (True, None, 0):
            with self.subTest(partial=partial): self.refuses(self.raw, partial=partial)

    def test_every_incomplete_prefix_refuses(self):
        for cut in range(len(self.raw)):
            with self.subTest(cut=cut): self.refuses(self.raw[:cut])

    def test_malformed_duplicate_nonfinite_and_oversized_refuse(self):
        for raw in (b"", None, self.events, b"\xff\n", b"{\n", b"{}\n"*2000,
                    self.raw + b"x"*codex_agent.MAX_PROVIDER_RECORD,
                    self.raw.replace(b'"type":"turn.started"', b'"type":"turn.started","type":"turn.started"'),
                    self.raw.replace(b'30920', b'NaN'),
                    b"["*1500+b"0"+b"]"*1500+b"\n"):
            with self.subTest(kind=type(raw).__name__): self.refuses(raw)

    def test_ordinary_activity_is_opaque_not_a_success_catalogue(self):
        import copy
        additions = [
            {"type":"item.completed", "item":{"id":"edit", "type":"file_change", "changes":[{"path":"answer.py"}], "future":True}},
            {"type":"item.updated", "item":{"id":"opaque", "type":"future_tool", "nested":{"type":"turn.failed"}}},
            {"type":"future.activity", "payload":{"model":"not-attribution"}},
        ]
        for middle in ([], additions, list(reversed(self.events[2:-1])),
                       self.events[2:4], self.events[2:-1] + self.events[2:-1]):
            with self.subTest(middle=middle):
                self.assertTrue(self.agent.provider_terminal(0, self.encoded(self.events[:2]+middle+self.events[-1:]), partial=False)["ok"])
        for field,value in (("exit_code",1),("status","failed"),("command","changed"),("aggregated_output",{})):
            events=copy.deepcopy(self.events);events[4]["item"][field]=value
            self.assertTrue(self.agent.provider_terminal(0,self.encoded(events),partial=False)["ok"])

    def test_lifecycle_and_item_envelopes_remain_structural(self):
        import copy
        for at in (0,1,len(self.events)-1):
            events=copy.deepcopy(self.events);events[at]["unknown"]=True
            self.refuses(self.encoded(events))
        for events in (self.events*2,self.events[1:],self.events[:1]+self.events[2:],
                       self.events[:-1],self.events+[self.events[-1]]):
            self.refuses(self.encoded(events))
        for activity in ({}, {"type":False}, {"type":"item.completed","item":None},
                         {"type":"item.started","item":{"id":None,"type":"file_change"}},
                         {"type":"turn.future"}):
            self.refuses(self.encoded(self.events[:2]+[activity]+self.events[-1:]))

    def test_explicit_fault_and_reroute_are_not_hidden_by_activity(self):
        from provider_policy.codex import stream_outcome
        for event in ({"type":"error","message":"fault"}, {"type":"turn.failed","error":{}},
                      {"type":"item.completed","item":{"id":"error","type":"error","message":"fault"}}):
            raw=self.encoded(self.events[:-1]+[event]+self.events[-1:])
            self.refuses(raw);self.assertEqual(stream_outcome(raw),"faulted")
        event={"type":"item.completed","item":{"id":"reroute","type":"error",
               "message":"model rerouted: requested -> alternate (HighRiskCyberActivity)"}}
        raw=self.encoded(self.events[:-1]+[event]+self.events[-1:])
        self.refuses(raw);self.assertEqual(stream_outcome(raw),"rerouted")

    def test_invalid_usage_refuses(self):
        import copy
        for usage in (None,{},dict(self.events[-1]["usage"], input_tokens=True),
                      dict(self.events[-1]["usage"], output_tokens=-1),
                      dict(self.events[-1]["usage"], output_tokens=1.5)):
            events=copy.deepcopy(self.events); events[-1]["usage"]=usage
            self.refuses(self.encoded(events))

    def test_terminal_words_inside_text_are_not_events(self):
        import copy
        events=copy.deepcopy(self.events[:-1])
        events[-1]["item"]["text"]='{"type":"turn.completed"}'
        self.refuses(self.encoded(events))

    def test_success_and_context_never_supply_contributors(self):
        import provider_policy as policy
        from provider_policy import attribution
        from tests.manager import codex_fixtures as fixture
        with fixture.simulated(policy):
            given=fixture.delivered(policy)
        for raw in (self.raw, (FIXTURES/"turn-context.projection.json").read_bytes(),
                    b'{"type":"result","subtype":"success","is_error":false,"modelUsage":{"fixture-reported":{}}}'):
            claim=attribution.record(given,phase="implementation",evidenced_build="0.169.0",raw=raw)
            self.assertEqual((claim["outcome"],claim["contributors"],claim["contributor_sources"]),("missing",[],{}))
            self.assertEqual(attribution.validate(claim,given,phase="implementation",raw=raw),claim)
            claim["contributors"]=["fixture-reported"]
            with self.assertRaises(policy.PolicyRefusal):
                attribution.validate(claim,given,phase="implementation",raw=raw)
