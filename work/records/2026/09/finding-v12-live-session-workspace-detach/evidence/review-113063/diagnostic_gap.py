"""Synthetic proof of information discarded by the existing reviewed listener.

No new diagnostic implementation, private-data read or provider invocation.
"""
import contextlib
import io
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import test_failure_reason_112817 as fixture

worker = fixture.worker
prior = fixture.prior
codes = ['authentication_failed', 'billing_error', 'rate_limit', 'invalid_request', 'server_error', 'unknown']
answers = []
for code in codes:
    assistant = dict(type='assistant', error=code, session_id=prior.SESSION,
                     message=dict(model=worker.ACTUAL_MODEL, content=[dict(type='text', text=prior.CANARY)]))
    result = dict(prior.ResultDiagnosticsTests().good(), is_error=True, api_error_status=None)
    supervisor = prior.prior.DiagnosticsTests().supervisor([assistant, result])
    assert type(supervisor) is worker.Supervisor
    supervisor.model = worker.ACTUAL_MODEL
    supervisor.limit = 1
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            supervisor.turn(dict(prompt=prior.CANARY))
        except worker.Refusal as error:
            refusal = worker.refusal_projection(error)
        else:
            raise AssertionError('failed result accepted')
    frames = [json.loads(line) for line in out.getvalue().splitlines()]
    assert prior.CANARY not in out.getvalue()
    normalized = [{k:v for k,v in row.items() if k != 'monotonic_ns'} for row in frames]
    assert normalized[-1]['failure_reason'] == dict(shape='null', http_status=None)
    assert refusal['refusal_code'] == 'provider-result-failed'
    answers.append(dict(synthetic_assistant_error=code, normalized_frames=normalized, refusal=refusal))
assert all(row['normalized_frames'] == answers[0]['normalized_frames'] and row['refusal'] == answers[0]['refusal'] for row in answers)
report = dict(claim=113063, current_listener_discards_all_six_categories=True, cases=answers,
              limitation='Synthetic documented assistant.error inputs, not recovered live frames or proof of fixed-image emission.',
              expected_gain='A future closed observation of this existing top-level field could distinguish categories even when result.api_error_status is null; no raw content is needed.')
with (HERE/'diagnostic-gap.json').open('x') as out:
    json.dump(report,out,indent=2)
    out.write('\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
