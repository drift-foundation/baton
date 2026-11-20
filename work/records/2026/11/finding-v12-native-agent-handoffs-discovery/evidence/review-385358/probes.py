"""Independent deterministic probes; run against the reconstructed candidate.
No product changes. Fixtures own their disposable repositories and stores.
"""
import json
import os
import unittest
from tests.tools.test_native_handoffs import HandoffJobCase, REQUEST
from tests.job_manager.test_native_handoffs import HandoffCase
from baton_v12.job_manager import native_handoffs

class ComposedProbes(HandoffJobCase):
    def test_zero_edit_yield_answer_resume(self):
        held = self.started()
        self.assertEqual(self.turn(held.control, 'implementation', held.attempt_id,
            held.roots, edits={'handoff/request.json': json.dumps(REQUEST)}), 0)
        self.drive(held.job, held.composed, 'implementation', native_handoffs.AWAITING_STATE)
        self.resumed(self.answered(held))
        self.assertEqual(len(self.messages()), 2)

    def test_retained_continuation_reaches_resumed_provider(self):
        held = self.resumed(self.answered(self.yielded()))
        seen = {}
        original = self.provider
        def instrumented(edits=None, status=0):
            import claude_agent
            run = original(edits, status)
            def capture(argv, **options):
                if argv[0] == claude_agent.PROVIDER_PROGRAM:
                    p = os.path.join(options['cwd'], 'handoff', claude_agent.HANDOFF_CONTINUATION)
                    seen['file_exists'] = os.path.isfile(p)
                    seen['prompt_has_continuation'] = REQUEST['continuation'] in argv[-1]
                    seen['prompt'] = argv[-1]
                return run(argv, **options)
            return capture
        self.provider = instrumented
        self.assertEqual(self.turn(held.control, 'implementation', held.resumed,
            held.resumed_roots, edits={'harness.py': "print('finished')\n"}), 0)
        print('CONTINUATION_OBSERVATION', json.dumps({k:v for k,v in seen.items() if k != 'prompt'}))
        self.assertTrue(seen['file_exists'] or seen['prompt_has_continuation'],
            'retained continuation is absent from both provider prompt and working copy')

class ReplayProbe(HandoffCase):
    def test_actual_continuation_retry_returns_same_receipt(self):
        held = self.yielded()
        self.answered(held)
        first = native_handoffs.advance_continuation(self.jobs, self.control,
            self.authority, job_id='job-a')
        again = native_handoffs.advance_continuation(self.jobs, self.control,
            self.authority, job_id='job-a')
        self.assertEqual(again, first)

class ForeignRequestProbe(HandoffCase):
    def test_response_from_work_a_cannot_answer_work_b(self):
        from tests.job_manager.test_native_handoffs import WRITER, REVIEWER, handoff_response
        from baton_v12.authority import messages
        from baton_v12.job_manager import review_driver
        from baton_v12.contracts import ContractRefusal
        held = self.yielded()
        self.authority.create_work('0000000a-W2', 'impl', operation_id='create-other', contract='baton.v12.contract/1')
        scope = self.authority.project_work('0000000a-W2')['scope']
        self.authority.grant_capability(REVIEWER, messages.ANSWER_CAPABILITY, scope=scope)
        self.authority.add_route_handler('impl', 'baton.other')
        other_producer = self.authority.session('baton.other')
        assignment = other_producer.claim({'work_id':'0000000a-W2','operation_id':'claim-other'})['assignment']
        original = held['message']
        other = other_producer.request_handoff({
            'expect':assignment, 'operation_id':'other-request', 'message_id':'other-request',
            'job_id':'other-job', 'kind':original['kind'], 'body':original['body'],
            'handoff_digest':original['handoff_digest'], 'task_digest':original['task_digest'],
            'checkpoint_ref':original['checkpoint_ref'],
            'continuation_digest':original['continuation_digest'], 'destination':REVIEWER})
        number = held['round']['generation']
        attempt = self.attempt('foreign-response-attempt', number, REVIEWER, 'foreign-response-principal')
        review_driver.prepare_review(self.control, checkpoint_id=held['checkpoint_id'],
            attempt_id=attempt, generation=number, reviewer_worker_id='foreign-response-worker', profile=self.profile)
        self.completed(attempt, review=True)
        document = handoff_response(other['message_id'], other['handoff_digest'], other['checkpoint_ref'])
        self.retained_response(attempt, generation=number, document=document)
        response = native_handoffs.classified_response(self.control, attempt)
        with self.assertRaises(ContractRefusal):
            self.port_for(REVIEWER).answer(attempt_id=attempt, response=response)

if __name__ == '__main__':
    unittest.main(verbosity=2)
