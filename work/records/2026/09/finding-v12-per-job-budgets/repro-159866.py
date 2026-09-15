"""Post-import timeout hold across real serving reopen; deterministic provider."""
import copy
import json
import subprocess
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from baton_v12.integration import execution, reconciliation, queue
from baton_v12.job_manager import sweep
from tests.job_manager import fixtures

case = tests.TheComposedHostVerificationUsesTheJobsCeiling()
blocks = []
block = execution.block_target
def blocking(*args, **kwargs):
    blocks.append(copy.deepcopy(kwargs))
    return block(*args, **kwargs)
def revision(row):
    return subprocess.run(['git', '-C', row['target_source']['path'], 'rev-parse', row['target_reference']], check=True, capture_output=True, text=True).stdout.strip()
try:
    case.setUp()
    with patch.object(execution, 'block_target', blocking):
        held, deployment, result_id, _ = case._post_import_failure(failing=True)
        row = reconciliation.result_of(deployment.integration, result_id)
        target_id = row['canonical_target_id']
        target = copy.deepcopy(queue.target_of(deployment.integration, target_id))
        entries = copy.deepcopy(queue.entries_of(deployment.integration, target_id))
        before_revision = revision(row)
        counts = (len(case.seen), case.materialized, len(blocks))
        assert counts == (1, 1, 1), counts
        assert target['state'] == 'blocked' and target['blocked_reason'] == 'post-import-verification-no-status', target
        engine = case.case.engine
        held.composed.close()
        held.job.close()
        held.control.close()
        with patch.object(type(case.case), 'quiescing', return_value=engine):
            job, control, composed = case.case.serving_two(**case.case.traversing(result_judgment_workers=case.case.judgment_workers()))
        for _ in range(6):
            sweep(job, composed, now=fixtures.NOW)
        again = case.case.deployment_of(composed)
        after_counts = (len(case.seen), case.materialized, len(blocks))
        after_row = reconciliation.result_of(again.integration, result_id)
        assert counts == after_counts, (counts, after_counts)
        assert queue.target_of(again.integration, target_id) == target
        assert queue.entries_of(again.integration, target_id) == entries
        assert after_row == row
        assert revision(after_row) == before_revision
        assert again.authority.receipt(row['derived_proposal_id'], 'integration') is None
        print(json.dumps({'counts_before_after': [counts, after_counts], 'result_state': row['state'], 'target_state': target['state'], 'blocked_reason': target['blocked_reason'], 'reference': before_revision, 'entries': entries, 'hold': target['blocked_account']}, indent=2))
finally:
    case.doCleanups()
