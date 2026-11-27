"""Durable main conversation acceptance, with deterministic provider seams.

The retained-result fixture uses real Authority, Job and custody owners and a
fake checkpoint profile. No service, engine, credential or live provider runs.
Inherited base failures are compared separately in the retained run evidence.
"""
import copy
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest import mock

from baton_v12 import native_handoff
from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore, main_thread, native_handoffs, episodes, reading
from baton_v12.worker_manager import ControlStore, review_cycles
from tests.job_manager import test_native_handoffs as fixture
from tools import instance, job_observation, job_tui, job_viewer

CHECKPOINT = "6ac23589f24aa94fe8cfd9cb7d79eb57d78d061c"
QUESTION = "M386412: launch.py repair site is outside the admitted scope; may implementation extend scope?"
ANSWER = "Extend scope to the launch.py repair site and retain the candidate."


class MainConversation(fixture.HandoffCase):
    def setUp(self):
        super().setUp()
        self.actor = dict(authority_uuid=self.AUTHORITY, participant=fixture.OWNER,
                          principal=self.authority.principal_of(fixture.OWNER), uid=os.getuid())
        # A deterministic profile keeps the selected historical checkpoint,
        # without reading or running the original deployment.
        freeze = self.profile.freeze

        def frozen(*args, **kwargs):
            result = freeze(*args, **kwargs)
            result['head'] = CHECKPOINT
            self.profile.held[kwargs['revision']] = result
            return dict(result)

        def validate(repository, evidence, *, current=False):
            self.assertIn(evidence, self.profile.held.values())
            self.assertEqual(evidence['head'], CHECKPOINT)

        self.profile.freeze = frozen
        self.profile.validate = validate

    def escalation(self, *, historical=False):
        request = fixture.handoff_request
        response = fixture.handoff_response

        def asking(*args, **kw):
            return dict(request(*args, **kw), body=QUESTION)

        def escalating(*args, **kw):
            result = response(*args, **kw)
            result.update(body="The repair requires an owner scope decision.", escalation={
                'ambiguity': 'launch.py is excluded but its repair is necessary',
                'options': ['extend scope', 'repair in a separate Job', 'retain the hold', 'cancel'],
                'recommendation': 'extend scope'})
            return result

        with mock.patch.object(fixture, 'handoff_request', asking), mock.patch.object(fixture, 'handoff_response', escalating):
            held = self.yielded(kind=native_handoff.FINDING_KIND)
            answered = self.answered(held, disposition='escalate')
        reply = answered['reply']['message']
        native_handoffs.record_hold(self.jobs, stage_id='job-a/implementation', episode=1,
            message_id=reply['message_id'], request_id=held['message']['message_id'],
            destination=fixture.OWNER, checkpoint_id=held['checkpoint_id'],
            **({} if historical else {'question': QUESTION}))
        return held, answered

    def answer(self, held, body=ANSWER, **kw):
        return main_thread.answer(self.jobs, self.authority, kw.pop('job_id', 'job-a'),
            held['message']['message_id'], body, phase='job-a/implementation',
            checkpoint_id=held['checkpoint_id'], actor=self.actor, **kw)

    def restart(self):
        self.jobs.close()
        self.control.close()
        self.jobs = JobStore.open(os.path.join(self.root, 'handoff-jobs.sqlite3'),
            authority_uuid=self.AUTHORITY, incarnation='restarted', clock=self.clock)
        self.control = ControlStore.open(os.path.join(self.root, 'control.sqlite3'),
            incarnation='restarted', clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.addCleanup(self.control.close)
        from baton_v12.worker_manager.workspaces import configure_workspace_storage
        configure_workspace_storage(self.control, self.storage)
        from tests.manager import input_roots
        self.group = input_roots.configured_group(self.control)

    def conversation(self):
        return main_thread.read(self.jobs, self.authority, 'job-a')

    def test_case_1_legacy_main_and_stable_identity(self):
        first = self.conversation()
        self.assertEqual(first['entries'], [])
        held, answered = self.escalation(historical=True)
        before = self.conversation()
        self.restart()
        self.assertEqual(before, self.conversation())
        self.assertEqual(first['thread_id'], before['thread_id'])
        self.assertEqual(before['name'], 'main')
        self.assertEqual([one['message_id'] for one in before['entries']],
                         [held['message']['message_id'], answered['reply']['message']['message_id']])
        self.assertEqual(main_thread.read(self.jobs, self.authority, 'job-a', thread='main'), before)
        with self.assertRaises(ContractRefusal):
            main_thread.read(self.jobs, self.authority, 'job-a', thread='side')

    def test_case_2_notes_order_authors_and_no_scheduling_effect(self):
        main_thread.note(self.jobs, self.authority, 'job-a', 'before request', actor=self.actor, operation_id='before')
        held, answered = self.escalation()
        states = self.states()
        note = main_thread.note(self.jobs, self.authority, 'job-a', 'retain this candidate', actor=self.actor, operation_id='after')
        self.assertEqual(self.states(), states)
        self.assertEqual(episodes.live_of(self.jobs, 'job-a/implementation')['episode'], 1)
        entries = self.conversation()['entries']
        self.assertEqual([one['author'] for one in entries], [fixture.OWNER, fixture.WRITER, fixture.REVIEWER, fixture.OWNER])
        self.assertEqual(entries[-1], note)
        self.assertEqual(entries[1]['phase'], 'job-a/implementation')
        self.assertEqual(entries[2]['phase'], 'job-a/review')
        self.assertIsNone(native_handoffs.continuation_of(self.jobs, 'job-a/implementation', 1))
        self.assertEqual(main_thread.note(self.jobs, self.authority, 'job-a', 'retain this candidate', actor=self.actor, operation_id='after'), note)

    def test_case_3_reconstruct_scope_escalation(self):
        held, answered = self.escalation()
        self.assertEqual(held['message']['kind'], 'finding-request')
        self.assertEqual(held['message']['body']['body'], QUESTION)
        self.assertEqual(held['checkpoint']['evidence']['head'], CHECKPOINT)
        self.assertEqual(held['record']['continuation'], fixture.CONTINUATION_TEXT)
        self.assertEqual(answered['reply']['message']['destination'], 'baton.slaw')
        self.assertEqual(answered['reply']['transition']['effect'], 'held')
        self.assertEqual(answered['document']['disposition'], 'escalate')
        self.assertEqual(len(answered['document']['escalation']['options']), 4)
        self.assertEqual(answered['document']['escalation']['recommendation'], 'extend scope')
        self.assertEqual(review_cycles.checkpoint_of(self.control, held['checkpoint_id'])['evidence'], held['checkpoint']['evidence'])

    def install_stopped(self):
        """An isolated local-owner instance layout, with no service processes."""
        root = Path(self.root, 'stopped')
        root.mkdir(mode=0o700)
        places = instance.layout(root)
        Path(places['stores']).mkdir()
        for source, destination, conn in (
            ('jobs', 'job_store', self.jobs._connection),
            ('control', 'control_store', self.control._connection)):
            import sqlite3
            with contextlib.closing(sqlite3.connect(places[destination])) as target:
                conn.backup(target)
        # Copy using SQLite backup so the Authority's WAL is included.
        import sqlite3
        with contextlib.closing(sqlite3.connect(Path(self.root, 'authority.sqlite3'))) as source:
            with contextlib.closing(sqlite3.connect(places['authority_store'])) as target:
                source.backup(target)
        Path(places['distro']).mkdir()
        Path(places['command']).write_text('deterministic fixture; never executed\n')
        Path(places['install_inputs']).write_text(json.dumps({'owner_participant': fixture.OWNER}))
        selected = instance.emit(root, authority_uuid=self.AUTHORITY, identity={'fixture': True},
                                     runtime=instance.manifest(places['distro']), now=self.clock())
        instance.create(places['instance'], selected)
        return places

    def client(self, places, args):
        # The child fails on any process/network start, including a manager,
        # publisher or worker. Imports precede the guard; the command does not.
        code = """
import sys
from tools import job_manager
from baton_v12.job_manager import main_thread

def audit(event, args):
    if event in ('subprocess.Popen', 'os.system', 'os.fork', 'os.posix_spawn', 'socket.connect'):
        raise AssertionError('stopped client attempted execution')
sys.addaudithook(audit)
raise SystemExit(job_manager.main(sys.argv[1:]))
"""
        done = subprocess.run([sys.executable, '-B', '-c', code, 'thread', '--instance', places['instance'], '--job', 'job-a', *args],
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_case_4_stopped_fresh_clients_default_cli_and_library(self):
        held, _ = self.escalation()
        places = self.install_stopped()
        noted = self.client(places, ['note', '--operation', 'offline-note', '--body', 'retain candidate'])
        self.assertEqual(noted['requests'][0]['state'], 'open')
        decided = self.client(places, ['answer', '--request', held['message']['message_id'], '--phase', 'job-a/implementation',
                                     '--checkpoint', held['checkpoint_id'], '--body', ANSWER])
        self.assertEqual(decided['requests'][0]['state'], 'answer-recorded')
        self.assertEqual(self.client(places, []), decided)
        with JobStore.open_readonly(places['job_store'], authority_uuid=self.AUTHORITY, incarnation='reader', clock=self.clock) as jobs:
            with Authority.open_readonly(places['authority_store'], expected_authority_uuid=self.AUTHORITY) as authority:
                self.assertEqual(main_thread.read(jobs, authority, 'job-a'), decided)
                self.assertIsNone(native_handoffs.continuation_of(jobs, 'job-a/implementation', 1))
        self.assertFalse(Path(places['state']).exists())

    def test_stopped_owner_can_replace_multiple_rulings_with_a_standing_answer(self):
        held, _ = self.escalation()
        places = self.install_stopped()
        def publish(key):
            return self.client(places, ['ruling', '--operation', key, '--body', key])['rulings'][-1]['message_id']
        one = publish('one')
        two = publish('two')
        args = ['answer', '--standing', '--request', held['message']['message_id'], '--phase', 'job-a/implementation',
                '--checkpoint', held['checkpoint_id'], '--body', ANSWER, '--supersedes', two, '--supersedes', one]
        result = self.client(places, args)
        self.assertEqual(self.client(places, args), result)
        self.assertEqual([r['status'] for r in result['rulings']], ['superseded', 'superseded', 'active'])
        self.assertEqual(result['rulings'][-1]['supersedes'], sorted([one, two]))
        self.assertEqual(result['requests'][0]['decision']['message_id'], result['rulings'][-1]['message_id'])

    def test_replacement_refuses_foreign_nonruling_and_missing_message_ids(self):
        from baton_v12.job_manager import submit
        from tests.job_manager import fixtures
        submit(self.jobs, fixtures.submission(submission_id='other', jobs=[fixtures.job('other')]))
        foreign = main_thread.ruling(self.jobs, self.authority, 'other', 'foreign', actor=self.actor, operation_id='r')
        note = main_thread.note(self.jobs, self.authority, 'job-a', 'note', actor=self.actor, operation_id='note')
        held, _ = self.escalation()
        plain = self.answer(held)
        for target in (foreign['message_id'], note['message_id'], plain['message_id'], 'missing'):
            with self.assertRaises(ContractRefusal):
                main_thread.ruling(self.jobs, self.authority, 'job-a', 'replacement', supersedes=[target],
                                   operation_id=target, actor=self.actor)
        self.assertEqual(self.conversation()['rulings'], [])

    def test_ruling_retries_bind_body_and_replacement_ids_and_respect_exchange_size(self):
        def publish(key, body, *ids):
            return main_thread.ruling(self.jobs, self.authority, 'job-a', body,
                                      operation_id=key, supersedes=ids, actor=self.actor)
        original = publish('first', 'Keep the original rule.')
        other = publish('other', 'A separate rule.')
        replacement = publish('replace', 'Apply both changes.', original['message_id'], other['message_id'])
        self.assertEqual(publish('replace', replacement['body'], other['message_id'], original['message_id']), replacement)
        for key, body, targets in [('replace', 'different text', replacement['supersedes']),
                                   ('replace', replacement['body'], [other['message_id']]),
                                   ('oversize', 'a' + chr(1) * 16000, [])]:
            with self.assertRaises(ContractRefusal):
                publish(key, body, *targets)
        self.assertEqual([r['message_id'] for r in self.conversation()['rulings'] if r['status']=='active'],
                         [replacement['message_id']])

    def test_case_5_status_json_and_tui_share_question_and_phase(self):
        held, _ = self.escalation()
        for recorded in (False, True):
            if recorded:
                self.answer(held)
            doc = reading.read_status(os.path.join(self.root, 'handoff-jobs.sqlite3'), authority_uuid=self.AUTHORITY,
                incarnation='reader', clock=self.clock, control_store=os.path.join(self.root, 'control.sqlite3'))
            doc = json.loads(json.dumps(doc))
            seen = job_observation.job_view(doc, doc['jobs'][0])
            self.assertEqual(seen['headline'], 'ANSWER RECORDED' if recorded else 'DECISION NEEDED')
            self.assertIn(QUESTION, seen['headline_reason'])
            self.assertIn('job-a/implementation', seen['headline_reason'])
            if recorded:
                self.assertIn('awaiting delivery', seen['headline_reason'])
            snap = job_viewer.Snapshot(doc, received_at=0)
            rendered = job_tui.frame(job_tui.State(), snap, 0, 0, 30, 300)
            self.assertIn(seen['headline'], str(rendered))
            self.assertIn(QUESTION, str(rendered))
            terminal = dict(doc['jobs'][0], mode='MANUAL', lifecycle='closed')
            self.assertEqual(job_observation.job_view(doc, terminal)['headline'], 'CLOSED')

    def test_cases_6_7_restart_same_job_exactly_once_and_conflict(self):
        held, answered = self.escalation()
        original = copy.deepcopy(self.conversation()['entries'])
        old_result = dict(self.control._connection.execute('SELECT * FROM outputs WHERE runtime_attempt_id = ?', (held['round']['attempt_id'],)).fetchone())
        decision = self.answer(held)
        self.assertEqual(self.answer(held), decision)
        self.restart()  # recording -> custody
        real = review_cycles.hold_owner_continuation

        def crash(*args, **kw):
            real(*args, **kw)
            raise RuntimeError('crash after custody committed')

        with mock.patch.object(review_cycles, 'hold_owner_continuation', crash):
            with self.assertRaises(RuntimeError):
                main_thread.reconcile(self.jobs, self.control, self.authority)
        self.restart()  # custody -> episode delivery
        main_thread.reconcile(self.jobs, self.control, self.authority)
        continued = native_handoffs.continuation_of(self.jobs, 'job-a/implementation', 1)
        self.assertIsNotNone(continued)
        self.restart()  # delivery -> attempt start
        main_thread.reconcile(self.jobs, self.control, self.authority)
        self.assertEqual(self.answer(held), decision)
        with self.assertRaises(ContractRefusal):
            self.answer(held, 'cancel instead')
        self.assertEqual(self.jobs._connection.execute('SELECT count(*) FROM jobs').fetchone()[0], 1)
        self.assertEqual(self.jobs._connection.execute('SELECT count(*) FROM operations WHERE kind=?', (native_handoffs.CONTINUE_KIND,)).fetchone()[0], 1)
        self.assertEqual(episodes.live_of(self.jobs, 'job-a/implementation')['episode'], 2)
        fresh = self.implementation_round(2, based=held['checkpoint_id'])
        context = self.delivered(fresh['attempt_id'], role='implementation', stage_id='job-a/implementation')
        self.assertEqual(context['continuation']['owner_decision'], decision)
        self.assertEqual(context['continuation']['text'], fixture.CONTINUATION_TEXT)
        self.assertEqual(context['continuation']['request'], held['message'])
        self.assertEqual(context['continuation']['reply'], answered['reply']['message'])
        self.assertEqual(context['job_id'], 'job-a')
        self.assertEqual(dict(self.control._connection.execute('SELECT * FROM outputs WHERE runtime_attempt_id = ?', (held['round']['attempt_id'],)).fetchone()), old_result)
        self.assertEqual(self.conversation()['entries'][:2], original)
        self.assertEqual(self.conversation()['requests'][0]['state'], 'delivered')
        self.assertEqual(review_cycles.checkpoint_of(self.control, held['checkpoint_id'])['evidence'], held['checkpoint']['evidence'])
        self.assertEqual(review_cycles.response_of(self.control, answered['attachment']['attachment_id']), answered['record'])
        self.assertEqual({row[0] for row in self.jobs._connection.execute('SELECT work_id FROM stages')}, {fixture.WORK_A})
        self.assertEqual(native_handoffs.delivered_of(self.control, fresh['attempt_id']), context)

    def test_case_8_target_one_request_and_refuse_wrong_job(self):
        held, _ = self.escalation()
        original = held['message']
        second = self.producer.request_handoff(dict(expect=self.assignment, operation_id='other-question', message_id='other-question',
            job_id='job-a', kind=original['kind'], body=original['body'], handoff_digest=original['handoff_digest'],
            task_digest=original['task_digest'], checkpoint_ref=original['checkpoint_ref'],
            continuation_digest=original['continuation_digest'], destination=fixture.REVIEWER))
        from baton_v12.job_manager import submit
        from tests.job_manager import fixtures
        submit(self.jobs, fixtures.submission(submission_id='second-job', jobs=[fixtures.job('wrong-job')]))
        before = self.conversation()
        with self.assertRaises(ContractRefusal):
            self.answer(held, job_id='wrong-job')
        self.assertEqual(self.conversation(), before)
        self.assertEqual(len(before['open_requests']), 2)
        self.answer(held)
        main_thread.reconcile(self.jobs, self.control, self.authority)
        after = self.conversation()
        self.assertEqual([one['request_id'] for one in after['open_requests']], [second['message_id']])
        self.assertIsNone(self.authority.work_message_reply(second['message_id']))
        self.assertIsNone(main_thread.decision_of(self.jobs, 'job-a', second['message_id']))


    def test_empty_manual_job_also_has_one_implicit_main(self):
        from baton_v12.job_manager import manual
        manual.create(self.jobs, 'study', {'scope': ['worker-task.txt'], 'wall_seconds': 100})
        before = main_thread.read(self.jobs, self.authority, 'study')
        self.assertEqual(before['name'], 'main')
        self.assertEqual(before['entries'], [])
        main_thread.note(self.jobs, self.authority, 'study', 'owner note', actor=self.actor, operation_id='manual-note')
        after = main_thread.read(self.jobs, self.authority, 'study')
        self.assertEqual(before['thread_id'], after['thread_id'])
        self.assertEqual(len(after['entries']), 1)

    def test_legacy_hold_reentry_preserves_original_record(self):
        held, answered = self.escalation(historical=True)
        before = native_handoffs.hold_of(self.jobs, 'job-a/implementation', 1)
        reread = native_handoffs.record_hold(self.jobs, stage_id='job-a/implementation', episode=1,
            message_id=answered['reply']['message']['message_id'], request_id=held['message']['message_id'],
            destination=fixture.OWNER, checkpoint_id=held['checkpoint_id'], question=QUESTION)
        self.assertEqual(before, reread)

    def test_cancelled_job_keeps_answer_without_releasing_custody(self):
        from baton_v12.job_manager import cancellation
        held, _ = self.escalation()
        self.answer(held)
        cancellation.request(self.jobs, job_id='job-a', reason='owner cancelled')
        self.restart()
        main_thread.reconcile(self.jobs, self.control, self.authority)
        self.assertIsNone(native_handoffs.continuation_of(self.jobs, 'job-a/implementation', 1))
        self.assertEqual(review_cycles.line_of(self.control, self.line['line_id'])['state'], 'review-ready')
        self.assertEqual(self.conversation()['requests'][0]['state'], 'answer-recorded')

    def test_status_uses_one_snapshot_when_answer_arrives_during_observation(self):
        from baton_v12.job_manager import projection
        held, _ = self.escalation()
        acts = self.acting()
        original = acts.observe

        def observing(stage):
            self.answer(held)
            return original(stage)

        with mock.patch.object(acts, 'observe', observing):
            doc = projection.status(self.jobs, acts, observed_at=self.clock())
        self.assertEqual(doc['jobs'][0]['owner_questions'][0]['state'], 'open')
        next_doc = projection.status(self.jobs, acts, observed_at=self.clock())
        self.assertEqual(next_doc['jobs'][0]['owner_questions'][0]['state'], 'answer-recorded')


from tests.tools import test_native_handoffs as composed_fixture


class ServingOwnerContinuation(composed_fixture.HandoffJobCase):
    def test_manager_restart_delivers_decision_to_one_fresh_attempt(self):
        """Real manager ticks and launch delivery, deterministic fake provider."""
        response = dict(composed_fixture.ESCALATION, body='The launch.py repair is outside scope.',
                        escalation={'ambiguity': 'launch.py is excluded',
                                    'options': ['extend scope', 'separate Job', 'hold', 'cancel'],
                                    'recommendation': 'extend scope'})
        with mock.patch.object(composed_fixture, 'REQUEST', dict(composed_fixture.REQUEST, body=QUESTION)):
            held = self.answered(self.yielded(kind=native_handoff.FINDING_KIND), response=response)
        self.drive(held.job, held.composed, 'review', native_handoffs.ANSWERED_STATE, ticks=12)
        before = self.messages()
        yielded = native_handoffs.yield_of(held.job, 'job-a/implementation', 1)
        authority = self.authority()
        actor = dict(authority_uuid=authority.authority_uuid, participant=composed_fixture.OWNER,
                     principal=authority.principal_of(composed_fixture.OWNER), uid=os.getuid())
        # Shut down the serving object before a fresh local client writes.
        held.composed.close()
        decision = main_thread.answer(held.job, authority, 'job-a', before[0]['message_id'], ANSWER,
            phase='job-a/implementation', checkpoint_id=yielded['checkpoint_id'], actor=actor)
        self.reconnected(held)
        self.resumed(held)
        deployment = self.deployment_of(held)
        context = json.loads(Path(held.resumed_roots['inputs'], 'handoff.json').read_text())
        self.assertEqual(context['continuation']['owner_decision'], decision)
        self.assertEqual(context['continuation']['request'], before[0])
        self.assertEqual(context['continuation']['reply'], before[1])
        self.assertEqual(context['continuation']['text'], yielded['continuation'])
        writer = review_cycles.writer_for_attempt(deployment.control, attempt_id=held.resumed,
                                                  generation=deployment.generation_of(held.resumed))
        self.assertEqual(writer['based_checkpoint_id'], yielded['checkpoint_id'])
        self.assertEqual(context['job_id'], 'job-a')
        self.assertEqual(self.messages(), before)
        from baton_v12.job_manager import sweep
        for _ in range(3):
            sweep(held.job, held.composed, now=composed_fixture.fixtures.NOW)
        self.assertEqual(self.operations(held.job, native_handoffs.CONTINUE_KIND), 1)
        self.assertEqual(len(self.attempts_of(held, 'implementation')), 1)
        self.assertEqual(held.job._connection.execute('SELECT count(*) FROM jobs').fetchone()[0], 1)


class TheResumedProviderIsToldTheOwnerDecision(composed_fixture.HandoffJobCase):
    """W386447: after an owner answer, the resumed provider is PROMPTED with the decision, not only delivered it."""

    def resumed_after_answer(self):
        response = dict(composed_fixture.ESCALATION, body='The launch.py repair is outside scope.',
                        escalation={'ambiguity': 'launch.py is excluded',
                                    'options': ['extend scope', 'separate Job'], 'recommendation': 'extend scope'})
        with mock.patch.object(composed_fixture, 'REQUEST', dict(composed_fixture.REQUEST, body=QUESTION)):
            held = self.answered(self.yielded(kind=native_handoff.FINDING_KIND), response=response)
        self.drive(held.job, held.composed, 'review', native_handoffs.ANSWERED_STATE, ticks=12)
        request = self.messages()[0]
        yielded = native_handoffs.yield_of(held.job, 'job-a/implementation', 1)
        authority = self.authority()
        actor = dict(authority_uuid=authority.authority_uuid, participant=composed_fixture.OWNER,
                     principal=authority.principal_of(composed_fixture.OWNER), uid=os.getuid())
        held.composed.close()
        main_thread.answer(held.job, authority, 'job-a', request['message_id'], ANSWER,
                           phase='job-a/implementation', checkpoint_id=yielded['checkpoint_id'], actor=actor)
        self.reconnected(held)
        return self.resumed(held)

    def test_the_resumed_prompt_carries_the_decision_after_the_reviewer_reply(self):
        held = self.resumed_after_answer()
        self.assertEqual(self.turn(held.control, 'implementation', held.resumed, held.resumed_roots,
                                   edits={'harness.py': "print('extended')\n"}), 0)
        prompt = self.prompts[-1]
        reply_at = prompt.index("THE REVIEWER'S REPLY (escalate):")
        decision_at = prompt.index("THE OWNER'S DECISION ON THAT ESCALATION (baton.slaw)")
        self.assertLess(reply_at, decision_at)
        self.assertIn(ANSWER, prompt[decision_at:])
        self.assertIn("under the owner's decision", prompt)
        self.assertNotIn("the requirements and the verification command are unchanged", prompt)

    def test_a_decision_about_another_request_is_refused_before_the_provider(self):
        held = self.resumed_after_answer()
        place = Path(held.resumed_roots['inputs'], 'handoff.json')
        document = json.loads(place.read_text())
        import claude_agent
        for change in ({'request_id': 'message-other'}, {'escalation_id': 'reply-other'}, {'body': ''}):
            with self.subTest(change=change):
                altered = copy.deepcopy(document)
                altered['continuation']['owner_decision'].update(change)
                with mock.patch.object(claude_agent, 'INPUT_ROOT', str(self.root)):
                    Path(self.root, 'handoff.json').write_text(json.dumps(altered))
                    with self.assertRaises(claude_agent.TaskRefusal):
                        claude_agent._handoff_context('implementation')

    def test_a_continuation_without_a_decision_keeps_its_prompt(self):
        held = self.answered(self.yielded())
        self.resumed(held)
        self.assertEqual(self.turn(held.control, 'implementation', held.resumed, held.resumed_roots,
                                   edits={'harness.py': "print('finished')\n"}), 0)
        prompt = self.prompts[-1]
        self.assertNotIn("THE OWNER'S DECISION", prompt)
        self.assertIn("the requirements and the verification command are unchanged", prompt)
