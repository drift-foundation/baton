"""Disjoint N4a draft: offline boundaries, not provider qualification.

Unregistered until the D-first join (M386027). Run with just test-one.
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
    return {"contract": {"adapter": {"context_label": {
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
                ("implementation", ["implementation", "review"], "0.169.0"),
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
        with mock.patch.object(claude_agent.ClaudeAgent, "_prepared_home") as parent:
            with self.assertRaises(codex_agent.TaskRefusal):
                self.agent._prepared_home(Path("/not-used"))
            parent.assert_not_called()
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
