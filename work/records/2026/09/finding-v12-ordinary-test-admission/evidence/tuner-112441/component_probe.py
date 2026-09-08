"""Retain the actual public admission account and exact Authority replay."""
import json
from pathlib import Path
import unittest
from tests.integration.test_driver import _OrdinaryAdmissionWorld
from baton_v12.worker_manager import load_manifest, retentions_of

case = unittest.TestCase()
try:
    world = _OrdinaryAdmissionWorld(case)
    world.assert_retained_history()
    evidence = world.evidence()
    first = world.admit()
    receipts = world.publisher.receipts(world.proposal_id)
    again = world.admit()
    case.assertEqual(first, again)
    case.assertEqual(world.publisher.receipts(world.proposal_id), receipts)
    report = {
        'actual_commands': world.command_runs, 'worker_disposition': world.answered['disposition'],
        'required_tests': world.required, 'observation': world.observation,
        'completion': world.completion, 'frozen': world.frozen,
        'retained_result': load_manifest(world.manager, world.frozen['manifest_digest'], 'resultManifest'),
        'intake': world.intake, 'retentions': retentions_of(world.manager, 'public-writer'),
        'published': world.published, 'accepted_checkpoint': world.ended['checkpoint_id'],
        'reopened_evidence': evidence, 'authority_receipts': receipts,
        'actual_receipt_calls': world.calls, 'admitted': first,
        'exact_replay': first == again, 'writer_destroy_calls': len(world.adapter.destroyed_with),
        'review_destroy_calls': len(world.review['adapter'].destroyed_with),
        'integration_execution': 'stopped after real durable admission, before execution',
        'seams': ['deterministic model and engine', 'existing manager-assignment transport',
                  'existing checkpoint profile fixture holding actual Git object names'],
    }
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'actual_commands': report['actual_commands'], 'admitted_state': first['state'],
                      'receipt_kinds': [row['kind'] for row in receipts], 'exact_replay': report['exact_replay']}, indent=2))
finally:
    case.doCleanups()
