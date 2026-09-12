"""Reproduce a read/import interleaving with real disposable owners; simulated workers."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from unittest import mock

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PROOF = HERE.parent.parent
REPO = Path('/home/sl/src/baton')
sys.path[:0] = [str(PROOF / 'prepared-152563'), str(REPO / 'v12/python/src'), str(REPO / 'v12/python')]
import accounting as a
from baton_v12.authority import Authority
from baton_v12.job_manager import status
from tests.tools import test_stage_execution as cases

began = time.monotonic()
fixture = cases.TwoBoundJobsTraverseServingAndCorrection('test_real_B_consumer_judges_frozen_reports_and_completes_both_jobs')
report = {'scope': 'Real disposable owners and ordinary fixture import; simulated engine/provider, no live execution.'}
try:
    fixture.setUp()
    held, deployment, result_id, result = fixture.pending_judgments()
    for execution in deployment.judges.values():
        fixture.judgment_turn(held, execution)
    config = deployment.given
    projected = status(held.job, held.composed, observed_at='2026-09-12T00:00:00.000Z')
    works = {binding['job_id'][-1]: binding['job_work_id'] for binding in config['job_bindings']}
    works.update({kind: one['deployment']['input_manifest']['work_ref']['work_id'] for kind, one in config['result_judgment_workers']['job-b'].items()})
    original = a.reconciliation.result_of
    fired = [False]
    with Authority.open_readonly(fixture.authority_path, expected_authority_uuid=config['authority_uuid']) as owner:
        claims = a.read_claims(owner, works)
        latest = max(a.instant(event['at']) for row in claims.values() for event in row['events']) + 100
        now = datetime.fromtimestamp(latest, timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        reader = a.BoundJudges(config, incarnation=projected['incarnation'], authority=owner, clock=lambda: now, control_path=fixture.control_path)
        def interleaved(store, key):
            answer = original(store, key)
            if not fired[0]:
                fired[0] = True
                report['read_result_state'] = answer['state']
                report['policy_before_import'] = owner.policy_generation()
                fixture.drive_job(held.job, held.composed, 'job-b', 'integration', 'completed', ticks=14)
                report['policy_after_import'] = owner.policy_generation()
                report['result_after_import'] = original(deployment.integration, result_id)['state']
                report['jobs_after_import'] = {job: fixture.states_for(held.job, held.composed, job)['integration'] for job in ('job-a', 'job-b')}
            return answer
        with mock.patch.object(a.reconciliation, 'result_of', side_effect=interleaved):
            try:
                reader.read(projected, claims)
                report['observer_outcome'] = 'returned'
            except Exception as failure:
                report['observer_outcome'] = type(failure).__name__
                report['observer_message'] = str(failure)
        assert fired[0] and report['read_result_state'] != 'imported'
        assert report['result_after_import'] == 'imported'
        assert report['jobs_after_import'] == {'job-a': 'completed', 'job-b': 'completed'}
        assert report['policy_after_import'] > report['policy_before_import']
        assert report['observer_outcome'] == 'AccountingError', report
finally:
    fixture.doCleanups()
    report['seconds'] = time.monotonic() - began
    (HERE / 'import-interleaving-confirmed.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
