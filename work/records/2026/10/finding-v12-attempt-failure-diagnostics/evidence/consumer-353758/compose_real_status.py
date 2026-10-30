"""Compose ONE REAL baton.v12.job-status/7 document through PRODUCT code.

W333486 packaged-command proof. The document below is produced by
`baton_v12.job_manager.projection.status` -- the production composer -- over a
REAL `JobStore` holding a REAL submitted Job whose implementation stage failed.
It is NOT a handwritten dict: `review-2026-10-22T17-31-33Z.md` requires "real
composition rather than handwritten mismatched fixture shapes", so the only
thing supplied by hand is the canonical OBSERVATION a deployment's control
plane would have recorded, through the accepted fixture's own `observed()`
helper in the real reader's shape.

Read-only with respect to everything outside its own temporary store: it opens
no deployment, contacts no engine or provider, reads no credential and starts
nothing.
"""
import json
import sys
from pathlib import Path

HERE = Path(sys.argv[1])          # the isolated candidate's v12/python
OUT = Path(sys.argv[2])           # where to write the composed document
sys.path[:0] = [str(HERE / 'src'), str(HERE), str(HERE / 'tests/job_manager')]

from baton_v12.job_manager import projection
from baton_v12.worker_manager import failure_cause
from baton_v12.job_manager.documents import STATUS_SCHEMA
from baton_v12.job_manager.submission import submit
from fixtures import NOW, FakeOperations, JobManagerCase, submission


class Compose(JobManagerCase):
    """Borrows the accepted fixture's real store construction, nothing else."""

    def runTest(self):                                    # pragma: no cover
        pass


case = Compose()
case.setUp()
try:
    jobs = case.store()
    acts = FakeOperations()
    held = submission()
    submit(jobs, held)
    stage_id = held['jobs'][0]['stages'][0].get('stage_id') \
        or next(iter(acts.observations), None)
    # Find the implementation stage the submission actually created.
    document = projection.status(jobs, acts, observed_at=NOW)
    stages = [one for entry in document['jobs'] for one in entry['stages']]
    implementation = next(one for one in stages
                          if one['kind'] == 'implementation')
    stage_id = implementation['stage_id']

    # THE FAILED ATTEMPT, as a deployment's control plane would have recorded
    # it: a start failure with a composed typed diagnostic, plus the
    # caller-visible recording degradation this parent must carry honestly.
    # THE OWNED SHAPE IS READ FROM PRODUCT CODE, never typed here: the first
    # attempt at this harness hard-coded a schema string and the production
    # seam REFUSED it, which is the seam working. The attempt id likewise
    # comes from the real stage rather than from a literal.
    attempt_id = implementation['attempt_id']
    # cause None is the HONEST HISTORICAL UNKNOWN the milestone requires:
    # `answer_of` maps it to 'unknown' and `absent_of` names which records are
    # missing. Nobody looked is a different fact from a cause that came back
    # unknown, and neither is a fabricated cause.
    diagnostic = {'schema': failure_cause.DIAGNOSTIC_SCHEMA,
                  'attempt_id': attempt_id,
                  'cause': None,
                  # THE PRODUCER'S OWN FOUR KINDS, spelled as
                  # failure_cause._compose emits them -- including the revoked
                  # record's domain/generation suffix.
                  'absent_records': [
                      'attempt.cessation-*:expiry-reclaim',
                      'attempt.cessation-*:cancellation',
                      'runtime.start-failed',
                      'runtime.preparation-failed',
                      'resource-token.revoked:workspace:66306:1:1']}
    assert failure_cause.answer_of(diagnostic) == 'unknown'
    assert len(failure_cause.absent_of(diagnostic)) == 5
    acts.observed(
        stage_id,
        claimed_by=True,
        diagnostics=diagnostic,
        diagnostic_degradation='the outcome record was not written: the '
                               'journal is unreachable')

    document = projection.status(jobs, acts, observed_at=NOW)
    assert document['schema'] == STATUS_SCHEMA, document['schema']
    OUT.write_text(json.dumps(document, indent=2, sort_keys=True,
                              default=str) + '\n')
    stage = next(one for entry in document['jobs'] for one in entry['stages']
                 if one['stage_id'] == stage_id)
    print(json.dumps({
        'schema': document['schema'],
        'composer': 'baton_v12.job_manager.projection.status',
        'handwritten': False,
        'stage_id': stage_id,
        'stage_state': stage['state'],
        'attempt_diagnostics_present': stage.get('attempt_diagnostics')
        is not None,
        'diagnostic_degradation_present': stage.get('diagnostic_degradation')
        is not None,
        'bytes': OUT.stat().st_size,
    }, indent=1, sort_keys=True))
finally:
    case.doCleanups()
