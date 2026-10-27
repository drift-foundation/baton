"""The reviewer's two counterexamples, re-aimed at candidate-362931.

`../review-362892/probe.py` is the script that refused candidate-362657. Its
`theft` case expects the foreign submission to SUCCEED, so against the
corrected bytes it raises and the script never finishes -- which is itself the
result, and `REVIEWER-PROBE-UNMODIFIED.stderr` beside this file keeps that
traceback. This is the same two constructions with the refusal caught, so both
outcomes can be read as data.

Nothing else differs: the imports, the interruption shape and the foreign
document are the reviewer's.
"""
import json

from tests.job_manager.test_creation import CreationCase, FakeBinding, JOB
from tests.job_manager.fixtures import submission, job
from baton_v12.job_manager import submit, stage_rows
from baton_v12.job_manager.creation import created_job_of
from baton_v12.contracts import ContractRefusal

results = []


def run(name, action):
    case = CreationCase()
    case.setUp()
    try:
        results.append({'case': name, **action(case)})
    finally:
        case.doCleanups()


def replay(c):
    first = c.created()
    c.derivation.answer['input_digest'] = 'sha256:' + '9' * 64
    c.derivation.calls = 0
    try:
        second = c.created()
        return {'replayed': second == first,
                'derivation_asked_on_replay': c.derivation.calls,
                'recorded_provenance_unchanged':
                    created_job_of(c.jobs, JOB)['resolution_digest']
                    == first['resolution_digest']}
    except ContractRefusal as caught:
        return {'replayed': False, 'code': caught.code,
                'message': caught.message}


def theft(c):
    class Stop(Exception):
        pass

    class Interrupted(FakeBinding):
        def create_binding(self, *args, **kwargs):
            super().create_binding(*args, **kwargs)
            raise Stop()

    c.binding = Interrupted()
    try:
        c.created()
    except Stop:
        pass
    before = created_job_of(c.jobs, JOB)
    try:
        foreign = submit(c.jobs, submission('foreign-submission',
                                            jobs=[job(JOB)]))
        stolen = {'accepted': foreign}
    except ContractRefusal as caught:
        stolen = {'refused': True, 'code': caught.code,
                  'durable': caught.durable, 'message': caught.message}
    # AND THE PROMISE IN THE INCOMPLETE REPORT: the same request again.
    held = c.created(binding=FakeBinding(bound=(JOB,)))
    return {'reserved_state': before['state'],
            'foreign_submission': stolen,
            'original_resume': 'completed',
            'resumed_job': held['job_id'],
            'recorded_stages': [row['stage_id'] for row in
                                stage_rows(c.jobs)]}


run('completed replay after deployment input changes', replay)
run('ordinary submit steals interrupted creation Job identity', theft)
print(json.dumps(results, indent=2))
