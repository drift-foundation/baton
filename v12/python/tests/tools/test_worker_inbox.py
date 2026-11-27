"""Job inbox acceptance over real Job, Authority and custody owners.

Provider and engine seams are deterministic; no live services are required.
The retained interleaving preserves main display order and tests the distinct
inbox publication cursor mandated by the owner.
"""
import os
from unittest import TestCase, mock

from baton_v12.job_manager import main_thread, worker_inbox, JobStore
from tests.job_manager import test_native_handoffs as fixture


class MainThreadCursorPrerequisite(fixture.HandoffCase):
    def test_inflight_note_is_published_after_the_fetched_request(self):
        actor = dict(authority_uuid=self.AUTHORITY, participant=fixture.OWNER,
                     principal=self.authority.principal_of(fixture.OWNER), uid=os.getuid())
        write = main_thread._write
        delivered = []

        def interleaved(store, kind, operation, operands, count):
            # note() has already captured its Authority-message count. Before
            # its Job-journal commit, a request commits and a reader fetches it.
            self.yielded()
            delivered.extend(worker_inbox.read(self.jobs, self.authority, 'job-a')['entries'])
            return write(store, kind, operation, operands, count)

        with mock.patch.object(main_thread, '_write', interleaved):
            note = main_thread.note(self.jobs, self.authority, 'job-a', 'owner note',
                                    actor=actor, operation_id='inflight-note')
        current = main_thread.read(self.jobs, self.authority, 'job-a')['entries']
        self.assertEqual(len(delivered), 1)
        self.assertEqual(len(current), 2)
        self.assertIn(note, current)
        # Main still displays the note before the request: this assertion
        # explicitly preserves the old display order instead of demanding a
        # stable display prefix (the superseded c1898051 expectation).
        self.assertEqual(current[0]['message_id'], note['message_id'])
        after = delivered[-1]['sequence']
        page = worker_inbox.read(self.jobs, self.authority, 'job-a', after=after)
        self.assertEqual([entry['message_id'] for entry in page['entries']], [note['message_id']])
        self.assertGreater(page['last_sequence'], after)
        self.assertEqual(worker_inbox.read(self.jobs, self.authority, 'job-a', after=page['last_sequence'])['entries'], [])
        self.assertEqual(worker_inbox.read(self.jobs, self.authority, 'job-a')['entries'], delivered + page['entries'])
        self.jobs.close()
        self.jobs = JobStore.open(os.path.join(self.root, 'handoff-jobs.sqlite3'), authority_uuid=self.AUTHORITY, incarnation='restarted', clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.assertEqual(worker_inbox.read(self.jobs, self.authority, 'job-a', after=after), page)
        self.assertEqual(main_thread.note(self.jobs, self.authority, 'job-a', 'owner note', actor=actor, operation_id='inflight-note'), note)
        self.assertEqual(worker_inbox.read(self.jobs, self.authority, 'job-a', after=after), page)


class InboxAcceptance(fixture.HandoffCase):
    def actor(self):
        return dict(authority_uuid=self.AUTHORITY, participant=fixture.OWNER,
                    principal=self.authority.principal_of(fixture.OWNER), uid=os.getuid())

    def note(self, name, job='job-a'):
        return main_thread.note(self.jobs, self.authority, job, name, actor=self.actor(), operation_id=name)

    def test_library_bounds_isolation_replay_and_delivery_evidence(self):
        import importlib.util
        import json
        from pathlib import Path
        from baton_v12.contracts import ContractRefusal
        from baton_v12.job_manager import submit
        from tests.job_manager.fixtures import job, stage, submission
        from baton_v12.worker_manager import exchange
        # Both Jobs use the same real Authority and Job owners, with services stopped.
        submit(self.jobs, submission('inbox-second', [job('job-b', [stage()])]))
        self.note('foreign-note', 'job-b')
        self.assertEqual(worker_inbox.read(self.jobs, self.authority, 'job-a')['entries'], [])
        one = self.note('first')
        first = worker_inbox.read(self.jobs, self.authority, 'job-a')
        self.assertEqual(len(first['entries']), 1)
        self.assertEqual(first['entries'][0]['author'], fixture.OWNER)
        self.assertEqual(first['entries'][0]['kind'], main_thread.NOTE)
        self.assertEqual(first['entries'][0]['message_id'], one['message_id'])
        worker_inbox.read(self.jobs, self.authority, 'job-b')
        self.note('second')
        second = worker_inbox.read(self.jobs, self.authority, 'job-a', after=first['last_sequence'])
        self.assertGreater(second['last_sequence'], first['last_sequence'] + 1)
        self.assertEqual([entry['body'] for entry in second['entries']], ['second'])
        for after in (-1, True, '0', None, 2**63, second['last_sequence']+1):
            with self.subTest(after=after), self.assertRaises(ContractRefusal):
                worker_inbox.read(self.jobs, self.authority, 'job-a', after=after)
        with self.assertRaises(ContractRefusal):
            worker_inbox.read(self.jobs, self.authority, 'absent')
        with self.assertRaises(ContractRefusal):
            worker_inbox.read(self.jobs, mock.Mock(authority_uuid='foreign'), 'job-a')
        for limit in (0, True, 129, '1'):
            with self.assertRaises(ContractRefusal):
                worker_inbox.read(self.jobs, self.authority, 'job-a', limit=limit)
        self.assertEqual(worker_inbox.read(self.jobs, self.authority, 'job-a', limit=1), first)
        start = worker_inbox.phase_start(self.jobs, self.authority, 'job-a', 'attempt-inbox')
        with self.assertRaises(ContractRefusal):
            worker_inbox.phase_start(self.jobs, self.authority, 'job-b', 'attempt-inbox')
        self.note('later')
        self.assertEqual(worker_inbox.phase_start(self.jobs, self.authority, 'job-a', 'attempt-inbox'), start)
        self.assertEqual(worker_inbox.phase_start(self.jobs, self.authority, 'job-a', 'next-attempt')['entries'][-1]['body'], 'later')
        delivery = exchange.materialize(os.path.join(self.root, 'inbox-exchange'), attempt_id='attempt-inbox', workspace_group=self.group)
        worker_inbox.exchange_tick(self.jobs, self.authority, 'job-a', delivery)
        foreign_delivery = exchange.materialize(os.path.join(self.root, 'other-inbox'), attempt_id='other-attempt', workspace_group=self.group)
        worker_inbox.exchange_tick(self.jobs, self.authority, 'job-b', foreign_delivery)
        self.assertEqual([entry['body'] for entry in worker_inbox.phase_start(self.jobs, self.authority, 'job-b', 'other-attempt')['entries']], ['foreign-note'])
        path = Path(__file__).resolve().parents[3] / 'worker' / 'worker_inbox.py'
        spec = importlib.util.spec_from_file_location('confined_inbox', path)
        worker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(worker)
        foreign = worker.fetch(0, command_root=foreign_delivery.command_root, event_root=foreign_delivery.event_root)
        self.assertEqual([entry['body'] for entry in foreign['entries']], ['foreign-note'])
        fetched = worker.fetch(first['last_sequence'], command_root=delivery.command_root, event_root=delivery.event_root)
        self.assertEqual([entry['body'] for entry in fetched['entries']], ['second', 'later'])
        worker_inbox.exchange_tick(self.jobs, self.authority, 'job-a', delivery)
        self.assertEqual(worker_inbox.fetched_of(self.jobs, 'job-a', delivery.attempt_id), fetched['last_sequence'])
        import worker_inbox as confined
        import scripted_agent
        import codex_agent
        import claude_agent
        self.assertIs(codex_agent.CodexAgent._provider, claude_agent.ClaudeAgent._provider)
        with mock.patch.multiple(confined, COMMAND_ROOT=delivery.command_root, EVENT_ROOT=delivery.event_root):
            agent = scripted_agent.ScriptedAgent()
            self.assertEqual(agent.work({}, [])['disposition'], 'completed')
            self.assertIn(confined.INSTRUCTIONS, agent.inbox_instructions)
            self.assertEqual([entry['body'] for page in agent.inbox_pages for entry in page['entries']], ['first', 'second', 'later'])
        evidence = Path(delivery.event_root) / 'inbox-fetched.json'
        for invalid in ({'attempt_id': 'foreign', 'last_sequence': 0},
                        {'attempt_id': delivery.attempt_id, 'last_sequence': 2**63},
                        {'attempt_id': delivery.attempt_id, 'last_sequence': True},
                        {'attempt_id': delivery.attempt_id, 'last_sequence': fetched['last_sequence']+1},
                        {'attempt_id': delivery.attempt_id, 'last_sequence': 0, 'extra': 1}):
            evidence.write_text(json.dumps(invalid))
            # W386413 R1: validation is unchanged and strict at its own
            # boundary, but the manager's tick contains the refusal to this
            # attempt: it is journalled there and the cursor is unchanged.
            with self.assertRaises(ContractRefusal) as caught:
                observed = exchange.observed_inbox(delivery)
                worker_inbox.record_fetched(self.jobs, 'job-a', delivery.attempt_id, observed)
            worker_inbox.exchange_tick(self.jobs, self.authority, 'job-a', delivery)
            self.assertEqual(worker_inbox.refused_of(self.jobs, 'job-a', delivery.attempt_id), str(caught.exception))
            self.assertEqual(worker_inbox.fetched_of(self.jobs, 'job-a', delivery.attempt_id), fetched['last_sequence'])
        evidence.write_text(' ' * 65537)
        with self.assertRaises(ContractRefusal):
            exchange.observed_inbox(delivery)
        worker_inbox.exchange_tick(self.jobs, self.authority, 'job-a', delivery)
        self.assertIn('wider than 65536 bytes', worker_inbox.refused_of(self.jobs, 'job-a', delivery.attempt_id))
        self.assertEqual(worker_inbox.fetched_of(self.jobs, 'job-a', delivery.attempt_id), fetched['last_sequence'])
        self.assertIsNone(worker_inbox.refused_of(self.jobs, 'job-b', foreign_delivery.attempt_id))
        evidence.write_text(json.dumps(dict(attempt_id=delivery.attempt_id, last_sequence=first['last_sequence'])))
        worker_inbox.exchange_tick(self.jobs, self.authority, 'job-a', delivery)
        self.assertEqual(worker_inbox.fetched_of(self.jobs, 'job-a', delivery.attempt_id), fetched['last_sequence'])
        for document in Path(delivery.command_root).glob('.inbox*.json'):
            text = document.read_text()
            for forbidden in ('job-b', 'foreign-note', self.AUTHORITY, 'authority_uuid', 'checkpoint_ref', 'actor'):
                self.assertNotIn(forbidden, text)



    def test_pages_are_bounded_and_the_retained_module_has_one_registration(self):
        import json
        from pathlib import Path
        for number in range(5):
            main_thread.note(self.jobs, self.authority, 'job-a', str(number) + 'x' * 16380,
                             actor=self.actor(), operation_id='bounded-' + str(number))
        first = worker_inbox.read(self.jobs, self.authority, 'job-a')
        self.assertLessEqual(len(json.dumps(first).encode()), worker_inbox.MAX_BYTES)
        self.assertEqual(len(first['entries']), 3)
        second = worker_inbox.read(self.jobs, self.authority, 'job-a', after=first['last_sequence'])
        self.assertEqual(len(second['entries']), 2)
        self.assertGreater(second['entries'][0]['sequence'], first['last_sequence'])
        registry = Path(__file__).resolve().parents[2] / 'tools' / 'parallel_test.py'
        self.assertEqual(registry.read_text().count('"tests.tools.test_worker_inbox"'), 1)

    def test_phase_start_journal_is_frozen_for_both_roles_and_empty_bytes_unchanged(self):
        import json
        from types import SimpleNamespace
        from baton_v12.job_manager import native_handoffs
        from tools.stage_execution import StageComposition
        deployment = SimpleNamespace(jobs=self.jobs, control=self.control, authority=self.authority)
        stage = dict(job_id='job-a', stage_id='job-a/implementation', episode=1, attempt_id='empty-start')
        implementation = StageComposition(deployment, role='implementation', worker_id='impl')
        empty = implementation.handoff_document_for(stage)
        expected = native_handoffs.delivered_context(self.jobs, self.control, self.authority, role='implementation', job_id='job-a', stage_id=stage['stage_id'], episode=1)
        self.assertEqual(empty, native_handoffs.context_bytes(expected))
        self.note('before-start')
        for role in ('implementation', 'review'):
            composition = StageComposition(deployment, role=role, worker_id=role)
            stage.update(stage_id='job-a/'+role, attempt_id=role+'-start')
            raw = composition.handoff_document_for(stage)
            page = worker_inbox.phase_start(self.jobs, self.authority, 'job-a', stage['attempt_id'])
            self.assertEqual(page['entries'][0]['body'], 'before-start')
            self.assertGreater(page['last_sequence'], 0)
            record = json.loads(self.jobs.operation_record('worker-inbox.start:' + stage['attempt_id'])['result'])
            self.assertEqual(record['page'], page)
            self.assertEqual(record['attempt_id'], stage['attempt_id'])
            self.assertEqual(native_handoffs.context_bytes(native_handoffs.delivered_of(self.control, stage['attempt_id'])), raw)
            self.assertEqual(composition.handoff_document_for(stage), raw)


from tests.tools import test_native_handoffs as composed_fixture


class SameTurnInbox(composed_fixture.HandoffJobCase):
    def test_note_fetched_before_candidate_in_same_attempt_and_after_restart(self):
        import worker_inbox as confined
        import claude_agent
        from baton_v12.job_manager import episodes, native_handoffs
        held = self.started()
        live = episodes.live_of(held.job, 'job-a/implementation')
        order = []
        provider = self.provider
        errors = []

        def scripted(*args, **kwargs):
            run = provider(*args, **kwargs)
            def invoke(argv, **options):
                try:
                    if argv[0] == claude_agent.PROVIDER_PROGRAM:
                        order.append('provider-started')
                        self.assertIn(confined.INSTRUCTIONS, argv[-1])
                        authority = self.authority()
                        actor = dict(authority_uuid=authority.authority_uuid, participant=composed_fixture.OWNER,
                                     principal=authority.principal_of(composed_fixture.OWNER), uid=os.getuid())
                        before = self.states(held.job, held.composed)
                        note = main_thread.note(held.job, authority, 'job-a', 'during this turn', actor=actor, operation_id='same-turn')
                        held.composed._inbox_tick()
                        self.assertEqual(self.states(held.job, held.composed), before)
                        launched = self.worker_of(held.composed, 'implementation')._adopted(dict(live, job_id='job-a', kind='implementation'))
                        page = confined.fetch(0, command_root=launched.exchange.command_root, event_root=launched.exchange.event_root)
                        self.assertEqual([entry['message_id'] for entry in page['entries']], [note['message_id']])
                        self.assertEqual(episodes.live_of(held.job, 'job-a/implementation'), live)
                        order.append('fetched')
                        held.composed._inbox_tick()
                        self.reconnected(held)
                        main_thread.note(held.job, authority, 'job-a', 'after restart', actor=actor, operation_id='after-restart')
                        held.composed._inbox_tick()
                        self.assertEqual(worker_inbox.fetched_of(held.job, 'job-a', held.attempt_id), page['last_sequence'])
                        newer = confined.fetch(page['last_sequence'], command_root=launched.exchange.command_root, event_root=launched.exchange.event_root)
                        self.assertEqual([entry['body'] for entry in newer['entries']], ['after restart'])
                        held.composed._inbox_tick()
                        self.assertEqual(confined.fetch(newer['last_sequence'], command_root=launched.exchange.command_root, event_root=launched.exchange.event_root)['entries'], [])
                        self.assertEqual(episodes.live_of(held.job, 'job-a/implementation'), live)
                        self.assertEqual(self.states(held.job, held.composed), before)
                        from baton_v12.job_manager import projection
                        from tools import job_observation, job_tui
                        import json
                        snapshot = projection.status(held.job, held.composed, observed_at=composed_fixture.fixtures.NOW)
                        snapshot = json.loads(json.dumps(snapshot))
                        job = next(one for one in snapshot['jobs'] if one['job_id'] == 'job-a')
                        stage = next(one for one in job['stages'] if one['kind'] == 'implementation')
                        self.assertEqual(stage['inbox_delivery']['attempts'][held.attempt_id], newer['last_sequence'])
                        view = job_observation.stage_view(stage, snapshot['observed_at'], job)
                        text = '\n'.join(job_observation.attempt_lines(view, detail=True))
                        self.assertIn('delivery only; comprehension and action unknown', text)
                        text = '\n'.join(job_tui._phase_block(view, True, 1000))
                        self.assertIn('delivery only; comprehension and action unknown', text)
                except Exception as failure:
                    import traceback
                    errors.append(traceback.format_exc())
                    raise
                return run(argv, **options)
            return invoke
        with mock.patch.object(self, 'provider', scripted):
            self.assertEqual(self.turn(held.control, 'implementation', held.attempt_id, held.roots,
                                      edits={'harness.py': "print('candidate after fetch')\n"}), 0, errors)
        order.append('candidate-handed-off')
        self.assertEqual(order, ['provider-started', 'fetched', 'candidate-handed-off'])
        authority = self.authority()
        actor = dict(authority_uuid=authority.authority_uuid, participant=composed_fixture.OWNER,
                     principal=authority.principal_of(composed_fixture.OWNER), uid=os.getuid())
        main_thread.note(held.job, authority, 'job-a', 'after ending', actor=actor, operation_id='after-ending')
        self.drive(held.job, held.composed, 'review', 'waiting')
        reviewer = self.only_attempt(held.composed, 'review')
        context = worker_inbox.phase_start(held.job, authority, 'job-a', reviewer)
        self.assertEqual([entry['body'] for entry in context['entries']], ['during this turn', 'after restart', 'after ending'])
        self.assertGreater(context['last_sequence'], 0)
        import copy
        import json
        report = copy.deepcopy(composed_fixture.composed.TheComposedJobTraversesReviewAndAcceptance.REPORT)
        self.assertEqual(self.turn(held.control, 'review', reviewer,
                                   self.mounted(held.composed, 'review', reviewer),
                                   edits={'review-report.json': json.dumps(report)}), 0)
        self.assertIn(confined.INSTRUCTIONS, self.prompts[-1])
        self.assertIn('after ending', self.prompts[-1])


class InboxPromptCompatibility(TestCase):
    def test_bound_prompt_and_argv_keep_exact_bytes_with_inbox_available(self):
        import baton_worker
        import claude_agent
        import worker_inbox as confined
        prompt = "Exact bound prompt with unicode: \u03bb\n"
        contextual = dict(model='fixture-model', mode='open', conversation_id='fixture-session')
        argv = [claude_agent.PROVIDER_PROGRAM, *claude_agent.PROVIDER_ARGUMENTS,
                '--model', contextual['model'], '--session-id', contextual['conversation_id'], prompt]
        contextual.update(prompt_digest=claude_agent._task_digest(prompt.encode()), argv_digest=baton_worker.digest(argv))
        agent = claude_agent.ClaudeAgent()
        class ReachedValidatedInvocation(Exception):
            pass
        with mock.patch.object(agent, '_context_bound', return_value=contextual), \
             mock.patch.object(agent, '_provider_selection', return_value=None), \
             mock.patch.object(agent, '_context_intent') as intent, \
             mock.patch.object(agent, '_context_result'), \
             mock.patch.object(agent, '_bound_activity', side_effect=ReachedValidatedInvocation), \
             mock.patch.object(confined, 'available', return_value=True), \
             mock.patch.object(confined, 'prompt') as addendum, \
             mock.patch.object(agent, 'provider_argv', wraps=agent.provider_argv) as rendered:
            with self.assertRaises(ReachedValidatedInvocation):
                agent._provider({}, claude_agent.OUTPUT_ROOT, None, None, prompt=prompt)
            rendered.assert_called_once_with(prompt)
            intent.assert_called_once_with(contextual)
            addendum.assert_not_called()
            # Keep the original integrity guard effective for changed bytes.
            with self.assertRaisesRegex(claude_agent.TaskRefusal, 'actual context prompt or argv disagrees'):
                agent._provider({}, claude_agent.OUTPUT_ROOT, None, None, prompt=prompt + 'changed')
            self.assertEqual(intent.call_count, 1)
        from baton_v12 import provider_policy
        from pathlib import Path
        canonical = Path(__file__).resolve().parents[4] / 'docs' / 'V12-WORKER-INSTRUCTIONS.md'
        self.assertEqual(provider_policy.worker_instructions(), canonical.read_bytes())
        self.assertIn(b'worker_inbox.py --after SEQUENCE', canonical.read_bytes())

    def test_unbound_prompt_addendum_requires_available_inbox(self):
        import claude_agent
        import worker_inbox as confined
        agent = claude_agent.ClaudeAgent()
        class ReachedInvocation(Exception):
            pass
        for available in (True, False):
            with self.subTest(available=available), \
                 mock.patch.object(agent, '_context_bound', return_value=None), \
                 mock.patch.object(agent, '_provider_selection', return_value=None), \
                 mock.patch.object(agent, '_bound_activity', side_effect=ReachedInvocation), \
                 mock.patch.object(confined, 'available', return_value=available), \
                 mock.patch.object(confined, 'prompt', return_value=' inbox addendum') as addendum, \
                 mock.patch.object(agent, 'provider_argv', wraps=agent.provider_argv) as rendered:
                with self.assertRaises(ReachedInvocation):
                    agent._provider({}, None, None, None, prompt='original')
                rendered.assert_called_once_with('original inbox addendum' if available else 'original')
                self.assertEqual(addendum.call_count, int(available))



from tests.tools import test_stage_execution as traversal


class ContainedAcknowledgement(traversal.TwoBoundJobsTraverseServingAndCorrection):
    """W386413 R1: a refused acknowledgement stays on its own attempt.

    Two bound Jobs code at once on their own producers. Job A's live attempt
    carries a worker-written inbox-fetched.json the manager refuses; ordinary
    sweeps and a manager restart keep serving. Job B receives its own inbox
    publication, records its own valid acknowledgement, completes its
    implementation after the restart and reaches review. A's refusal stays
    visible on A's attempt, A's cursor is unchanged, and a later valid
    acknowledgement from A is still recorded. Inherited traversal cases are
    not collected here; they run in their own module only.
    """

    def exchange_of(self, held, job_id, attempt_id, kind="implementation"):
        from baton_v12.job_manager import episodes
        worker_id, _prepared = self.preparing(held.composed, attempt_id)
        worker = {one["worker_id"]: one for one in held.composed.workers}[worker_id]["operations"]._worker
        live = episodes.live_of(held.job, job_id + "/" + kind)
        self.assertEqual(live["attempt_id"], attempt_id)
        return worker._adopted(dict(live, job_id=job_id, kind=kind)).exchange

    def sweeps(self, held, count=3):
        from baton_v12.job_manager import sweep
        for _ in range(count):
            sweep(held.job, held.composed, now=traversal.NOW)

    def restarted(self, held):
        from tools import stage_execution
        composed = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base, **self.traversing()),
            held.job, held.control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: traversal.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        held.composed = composed
        return held

    def test_refused_acknowledgement_is_contained_across_sweeps_and_restart(self):
        import json
        import worker_inbox as confined
        from baton_v12.authority import Authority
        from baton_v12.contracts import ContractRefusal
        from baton_v12.job_manager import manager, projection
        from tools import job_observation, job_tui
        held = self.coding()
        a_exchange = self.exchange_of(held, "job-a", held.first)
        b_exchange = self.exchange_of(held, "job-b", held.second)
        # Job A's worker writes an acknowledgement outside the helper's contract.
        claimed = {"attempt_id": held.first, "last_sequence": 2**40}
        with open(os.path.join(a_exchange.event_root, "inbox-fetched.json"), "w") as handle:
            json.dump(claimed, handle)
        authority = Authority.open(self.authority_path, expected_authority_uuid=self.config["authority_uuid"])
        self.addCleanup(authority.dispose)
        participant = self.config["participant"]
        actor = dict(authority_uuid=authority.authority_uuid, participant=participant,
                     principal=authority.principal_of(participant), uid=os.getuid())
        note = main_thread.note(held.job, authority, "job-b", "for job b", actor=actor, operation_id="job-b-note")
        self.sweeps(held)
        reason = worker_inbox.refused_of(held.job, "job-a", held.first)
        self.assertIn("not published to this attempt", reason)
        self.assertIsNone(worker_inbox.fetched_of(held.job, "job-a", held.first))
        # Validation itself is unchanged and strict at the library boundary.
        with self.assertRaises(ContractRefusal):
            worker_inbox.record_fetched(held.job, "job-a", held.first, claimed)
        # Job B was served on the same sweeps: its publication reached its own
        # exchange, and its own valid acknowledgement is recorded.
        page = confined.fetch(0, command_root=b_exchange.command_root, event_root=b_exchange.event_root)
        self.assertEqual([one["message_id"] for one in page["entries"]], [note["message_id"]])
        self.sweeps(held, count=1)
        self.assertEqual(worker_inbox.fetched_of(held.job, "job-b", held.second), page["last_sequence"])
        self.assertIsNone(worker_inbox.refused_of(held.job, "job-b", held.second))
        # Job B's implementation completes on ordinary sweeps while A's
        # refusal is evaluated on every one of them.
        self.produced(held, "job-b", held.second, self.B_FEATURE,
                      edits={"feature.py": self.B_FEATURE, "feature_check.py": self.B_CHECK})
        # A manager restart over the same stores: reconcile and sweeps serve on,
        # and Job B's review is reached and delivered B's own inbox at phase start.
        self.restarted(held)
        manager.reconcile(held.job, held.composed, now=traversal.NOW)
        self.drive_job(held.job, held.composed, "job-b", "review", "waiting")
        reviewer = self.one_attempt_of(held.composed, "review-worker-b")
        start = worker_inbox.phase_start(held.job, authority, "job-b", reviewer)
        self.assertEqual([one["message_id"] for one in start["entries"]], [note["message_id"]])
        # A's refusal is still visible on A's attempt, its cursor unchanged,
        # and A's own stage was not ended or held by it.
        self.assertEqual(self.states_for(held.job, held.composed, "job-a")["implementation"], "waiting")
        self.assertIsNone(worker_inbox.fetched_of(held.job, "job-a", held.first))
        snapshot = json.loads(json.dumps(projection.status(held.job, held.composed, observed_at=traversal.NOW)))
        a_job = next(one for one in snapshot["jobs"] if one["job_id"] == "job-a")
        stage = next(one for one in a_job["stages"] if one["kind"] == "implementation")
        self.assertEqual(stage["inbox_delivery"]["refused"], {held.first: reason})
        self.assertNotIn(held.first, stage["inbox_delivery"]["attempts"])
        view = job_observation.stage_view(stage, snapshot["observed_at"], a_job)
        text = "\n".join(job_observation.attempt_lines(view, detail=True))
        self.assertIn("inbox acknowledgement refused: inbox evidence names a sequence not published to this attempt", text)
        self.assertIn("fetch cursor unchanged", text)
        self.assertIn("inbox acknowledgement refused: ", "\n".join(job_tui._phase_block(view, True, 1000)))
        b_job = next(one for one in snapshot["jobs"] if one["job_id"] == "job-b")
        self.assertNotIn("refused", next(one for one in b_job["stages"] if one["kind"] == "implementation")["inbox_delivery"])
        # A later valid acknowledgement from A is still recorded; the refusal
        # remains as that attempt's history.
        os.remove(os.path.join(a_exchange.event_root, "inbox-fetched.json"))
        valid = confined.fetch(0, command_root=a_exchange.command_root, event_root=a_exchange.event_root)
        self.sweeps(held, count=1)
        self.assertEqual(worker_inbox.fetched_of(held.job, "job-a", held.first), valid["last_sequence"])
        self.assertEqual(worker_inbox.refused_of(held.job, "job-a", held.first), reason)


# Inherited traversal cases belong to tests.tools.test_stage_execution alone.
for _name in dir(traversal.TwoBoundJobsTraverseServingAndCorrection):
    if _name.startswith("test_") and _name not in vars(ContainedAcknowledgement):
        setattr(ContainedAcknowledgement, _name, None)
del _name
